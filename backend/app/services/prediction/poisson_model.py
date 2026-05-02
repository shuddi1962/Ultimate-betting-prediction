import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import Fixture, Prediction, TeamXGHistory, Team, MatchStatistics


class PoissonModel:
    """Dixon-Coles Poisson model for score prediction"""
    
    def __init__(self):
        self.lambda_home = 0.0
        self.lambda_away = 0.0
        self.rho = 0.1
        self.home_advantage = 1.15
    
    def fit(self, home_goals_avg: float, away_goals_avg: float, 
            home_conceded_avg: float, away_conceded_avg: float,
            home_advantage: float = 1.15):
        """Fit model parameters from team averages"""
        league_avg_goals = (home_goals_avg + away_goals_avg + home_conceded_avg + away_conceded_avg) / 4
        
        self.home_attack = home_goals_avg / league_avg_goals
        self.away_attack = away_goals_avg / league_avg_goals
        self.home_defense = home_conceded_avg / league_avg_goals
        self.away_defense = away_conceded_avg / league_avg_goals
        self.home_advantage = home_advantage
    
    def predict_score_matrix(self, max_goals: int = 6) -> np.ndarray:
        """Generate probability matrix for all scorelines 0-0 to max_goals-max_goals"""
        matrix = np.zeros((max_goals + 1, max_goals + 1))
        
        lambda_home = self.home_attack * self.away_defense * self.home_advantage
        lambda_away = self.away_attack * self.home_defense
        
        from scipy.stats import poisson
        
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                p = poisson.pmf(h, lambda_home) * poisson.pmf(a, lambda_away)
                
                # Dixon-Coles correction for low scorelines
                if h == 0 and a == 0:
                    p *= (1 + self.rho)
                elif h == 1 and a == 0:
                    p *= (1 - self.rho)
                elif h == 0 and a == 1:
                    p *= (1 - self.rho)
                elif h == 1 and a == 1:
                    p *= (1 + self.rho)
                
                matrix[h, a] = p
        
        # Normalize
        matrix = matrix / matrix.sum()
        return matrix
    
    def get_result_probs(self, matrix: np.ndarray) -> Dict[str, float]:
        """Calculate home/draw/away probabilities from score matrix"""
        home_win = np.sum(np.tril(matrix, -1))
        draw = np.sum(np.diag(matrix))
        away_win = np.sum(np.triu(matrix, 1))
        
        return {
            "home": float(home_win),
            "draw": float(draw),
            "away": float(away_win),
        }
    
    def get_goal_probs(self, matrix: np.ndarray) -> Dict[str, float]:
        """Calculate over/under probabilities"""
        total_goals = np.sum(matrix * np.add.outer(np.arange(matrix.shape[0]), np.arange(matrix.shape[1])))
        
        over_2_5 = 0.0
        over_1_5 = 0.0
        over_3_5 = 0.0
        
        for h in range(matrix.shape[0]):
            for a in range(matrix.shape[1]):
                total = h + a
                p = matrix[h, a]
                if total > 2.5:
                    over_2_5 += p
                if total > 1.5:
                    over_1_5 += p
                if total > 3.5:
                    over_3_5 += p
        
        return {
            "over_2_5": float(over_2_5),
            "over_1_5": float(over_1_5),
            "over_3_5": float(over_3_5),
            "expected_goals": float(total_goals),
        }
