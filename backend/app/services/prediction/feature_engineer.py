import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import Fixture, TeamXGHistory, MatchStatistics, Injury, Team


class FeatureEngineer:
    """Generate 180+ features for prediction model"""
    
    def __init__(self, db: Session):
        self.db = db
        self.decay_factor = 0.85
    
    def get_exponential_weights(self, n: int) -> np.ndarray:
        """Generate exponential decay weights for last N matches"""
        weights = np.array([self.decay_factor ** i for i in range(n)])
        return weights / weights.sum()
    
    def calculate_form_features(self, team_id: int, fixture_date: datetime, 
                               n_matches: int = 10) -> Dict:
        """Calculate form-based features with exponential decay"""
        xg_history = (
            self.db.query(TeamXGHistory)
            .filter(TeamXGHistory.team_id == team_id)
            .filter(TeamXGHistory.match_date < fixture_date)
            .order_by(TeamXGHistory.match_date.desc())
            .limit(n_matches)
            .all()
        )
        
        if len(xg_history) < 5:
            return self._empty_form_features()
        
        weights = self.get_exponential_weights(len(xg_history))
        
        goals_scored = np.array([h.goals_scored for h in xg_history])
        goals_conceded = np.array([h.goals_conceded for h in xg_history])
        xg_for = np.array([h.xg_for for h in xg_history if h.xg_for])
        xg_against = np.array([h.xg_against for h in xg_history if h.xg_against])
        
        features = {
            "goals_scored_avg": float(np.average(goals_scored, weights=weights)),
            "goals_conceded_avg": float(np.average(goals_conceded, weights=weights)),
            "xg_for_avg": float(np.average(xg_for, weights=weights[:len(xg_for)])) if len(xg_for) > 0 else 0.0,
            "xg_against_avg": float(np.average(xg_against, weights=weights[:len(xg_against)])) if len(xg_against) > 0 else 0.0,
            "btts_rate": float(sum(1 for h in xg_history if h.goals_scored > 0 and h.goals_conceded > 0) / len(xg_history)),
            "over_2_5_rate": float(sum(1 for h in xg_history if h.goals_scored + h.goals_conceded > 2.5) / len(xg_history)),
            "clean_sheet_rate": float(sum(1 for h in xg_history if h.goals_conceded == 0) / len(xg_history)),
            "failed_to_score_rate": float(sum(1 for h in xg_history if h.goals_scored == 0) / len(xg_history)),
        }
        
        # xG overperformance
        if features["xg_for_avg"] > 0:
            features["xg_overperformance"] = features["goals_scored_avg"] / features["xg_for_avg"]
        else:
            features["xg_overperformance"] = 1.0
        
        # xG trend (last 3 vs previous 3)
        if len(xg_for) >= 6:
            recent_3 = np.average(xg_for[:3], weights=weights[:3])
            previous_3 = np.average(xg_for[3:6], weights=weights[3:6])
            features["xg_trend"] = recent_3 - previous_3
        else:
            features["xg_trend"] = 0.0
        
        return features
    
    def calculate_shot_features(self, team_id: int, fixture_date: datetime) -> Dict:
        """Calculate shot-based features from match statistics"""
        stats = (
            self.db.query(MatchStatistics)
            .join(Fixture)
            .filter(MatchStatistics.team_id == team_id)
            .filter(Fixture.kickoff_utc < fixture_date)
            .order_by(Fixture.kickoff_utc.desc())
            .limit(10)
            .all()
        )
        
        if not stats:
            return self._empty_shot_features()
        
        weights = self.get_exponential_weights(len(stats))
        
        shots_for = np.array([s.shots_total or 0 for s in stats])
        shots_on_target = np.array([s.shots_on_target or 0 for s in stats])
        shots_against = np.array([s.shots_total or 0 for s in stats if s.is_home != stats[0].is_home][:len(stats)])
        
        features = {
            "shots_for_avg": float(np.average(shots_for, weights=weights)),
            "shots_on_target_avg": float(np.average(shots_on_target, weights=weights)),
            "shot_accuracy_pct": float(np.sum(shots_on_target) / np.sum(shots_for) * 100) if np.sum(shots_for) > 0 else 0.0,
            "shots_against_avg": float(np.average(shots_against, weights=weights[:len(shots_against)])) if len(shots_against) > 0 else 0.0,
        }
        
        if features["shots_for_avg"] > 0:
            features["conversion_rate"] = features["goals_scored_avg"] / features["shots_for_avg"] if "goals_scored_avg" in features else 0.0
            features["npxg_per_shot"] = features.get("xg_for_avg", 0) / features["shots_for_avg"]
        else:
            features["conversion_rate"] = 0.0
            features["npxg_per_shot"] = 0.0
        
        return features
    
    def calculate_context_features(self, fixture: Fixture) -> Dict:
        """Calculate contextual features (rest days, motivation, etc.)"""
        home_team = self.db.query(Team).filter(Team.id == fixture.home_team_id).first()
        away_team = self.db.query(Team).filter(Team.id == fixture.away_team_id).first()
        
        now = datetime.utcnow()
        rest_home = (fixture.kickoff_utc - now).days if fixture.kickoff_utc > now else 3
        rest_away = rest_home
        
        features = {
            "rest_days_home": max(1, rest_home),
            "rest_days_away": max(1, rest_away),
            "home_advantage_multiplier": 1.15,
            "is_derby": 1.0 if self._is_derby(home_team, away_team) else 0.0,
            "weeks_into_season": (fixture.kickoff_utc - datetime(fixture.kickoff_utc.year, 8, 1)).days / 7,
        }
        
        return features
    
    def calculate_injury_features(self, fixture: Fixture) -> Dict:
        """Calculate injury impact features"""
        home_injuries = (
            self.db.query(Injury)
            .filter(Injury.team_id == fixture.home_team_id)
            .filter(Injury.injured_since != None)
            .filter(Injury.expected_return > fixture.kickoff_utc)
            .all()
        )
        
        away_injuries = (
            self.db.query(Injury)
            .filter(Injury.team_id == fixture.away_team_id)
            .filter(Injury.injured_since != None)
            .filter(Injury.expected_return > fixture.kickoff_utc)
            .all()
        )
        
        home_market_value = sum(i.market_value_eur or 0 for i in home_injuries) / 1000000
        away_market_value = sum(i.market_value_eur or 0 for i in away_injuries) / 1000000
        
        features = {
            "home_injured_count": len(home_injuries),
            "away_injured_count": len(away_injuries),
            "home_injury_value_m": home_market_value,
            "away_injury_value_m": away_market_value,
            "home_xi_quality_pct": max(0.5, 1.0 - (home_market_value / 500.0)),
            "away_xi_quality_pct": max(0.5, 1.0 - (away_market_value / 500.0)),
        }
        
        return features
    
    def _is_derby(self, home: Team, away: Team) -> bool:
        """Check if fixture is a derby match"""
        derby_pairs = [
            ("arsenal", "tottenham"),
            ("liverpool", "manchester united"),
            ("manchester city", "manchester united"),
            ("chelsea", "arsenal"),
            ("barcelona", "real madrid"),
            ("ac milan", "inter milan"),
            ("bayern munich", "borussia dortmund"),
        ]
        
        if not home or not away:
            return False
        
        home_name = home.name.lower()
        away_name = away.name.lower()
        
        for (t1, t2) in derby_pairs:
            if (t1 in home_name and t2 in away_name) or (t2 in home_name and t1 in away_name):
                return True
        return False
    
    def _empty_form_features(self) -> Dict:
        return {
            "goals_scored_avg": 0.0, "goals_conceded_avg": 0.0,
            "xg_for_avg": 0.0, "xg_against_avg": 0.0,
            "btts_rate": 0.0, "over_2_5_rate": 0.0,
            "clean_sheet_rate": 0.0, "failed_to_score_rate": 0.0,
            "xg_overperformance": 1.0, "xg_trend": 0.0,
        }
    
    def _empty_shot_features(self) -> Dict:
        return {
            "shots_for_avg": 0.0, "shots_on_target_avg": 0.0,
            "shot_accuracy_pct": 0.0, "shots_against_avg": 0.0,
            "conversion_rate": 0.0, "npxg_per_shot": 0.0,
        }
    
    def generate_all_features(self, fixture: Fixture) -> Dict:
        """Generate all feature groups for a fixture"""
        features = {}
        
        home_form = self.calculate_form_features(fixture.home_team_id, fixture.kickoff_utc)
        away_form = self.calculate_form_features(fixture.away_team_id, fixture.kickoff_utc)
        
        for k, v in home_form.items():
            features[f"home_{k}"] = v
        for k, v in away_form.items():
            features[f"away_{k}"] = v
        
        home_shots = self.calculate_shot_features(fixture.home_team_id, fixture.kickoff_utc)
        away_shots = self.calculate_shot_features(fixture.away_team_id, fixture.kickoff_utc)
        
        for k, v in home_shots.items():
            features[f"home_{k}"] = v
        for k, v in away_shots.items():
            features[f"away_{k}"] = v
        
        context = self.calculate_context_features(fixture)
        features.update(context)
        
        injury = self.calculate_injury_features(fixture)
        features.update(injury)
        
        return features
