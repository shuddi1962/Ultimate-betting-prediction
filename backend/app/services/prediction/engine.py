import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import Fixture, Prediction
from .poisson_model import PoissonModel
from .feature_engineer import FeatureEngineer
from .confidence import ConfidenceCalculator


class PredictionEngine:
    """Main prediction engine that combines all models"""
    
    def __init__(self, db: Session):
        self.db = db
        self.poisson = PoissonModel()
        self.feature_engineer = FeatureEngineer(db)
        self.confidence_calc = ConfidenceCalculator(db)
    
    def generate_prediction(self, fixture: Fixture, data_sources_used: List[str]) -> Optional[Prediction]:
        """Generate full prediction for a fixture"""
        
        if fixture.status not in ['NS', 'TBD']:
            return None
        
        home_features = self.feature_engineer.calculate_form_features(
            fixture.home_team_id, fixture.kickoff_utc
        )
        away_features = self.feature_engineer.calculate_form_features(
            fixture.away_team_id, fixture.kickoff_utc
        )
        
        if home_features.get("goals_scored_avg", 0) == 0 and away_features.get("goals_scored_avg", 0) == 0:
            return None
        
        poisson_probs = self._run_poisson_model(home_features, away_features)
        
        model_probs = {
            "home": poisson_probs["home"],
            "draw": poisson_probs["draw"],
            "away": poisson_probs["away"],
        }
        
        confidence_data = self.confidence_calc.calculate_confidence(
            fixture, home_features, away_features, model_probs, data_sources_used
        )
        
        goal_probs = self.poisson.get_goal_probs(
            self.poisson.predict_score_matrix()
        )
        
        recommendation = self._generate_recommendation(poisson_probs, goal_probs, confidence_data)
        
        explanation = self._generate_explanation(fixture, home_features, away_features, poisson_probs)
        
        prediction = Prediction(
            fixture_id=fixture.id,
            home_win_prob=poisson_probs["home"],
            draw_prob=poisson_probs["draw"],
            away_win_prob=poisson_probs["away"],
            expected_home_goals=poisson_probs.get("expected_home", 0),
            expected_away_goals=poisson_probs.get("expected_away", 0),
            expected_total_goals=goal_probs["expected_goals"],
            btts_yes_prob=self._calculate_btts_prob(home_features, away_features),
            over_2_5_prob=goal_probs["over_2_5"],
            over_1_5_prob=goal_probs["over_1_5"],
            over_3_5_prob=goal_probs["over_3_5"],
            recommended_market=recommendation["market"],
            recommended_pick=recommendation["pick"],
            confidence_score=confidence_data["overall_confidence"],
            primary_reason=explanation["primary_reason"],
            why_not_home=explanation["why_not_home"],
            why_not_draw=explanation["why_not_draw"],
            why_not_away=explanation["why_not_away"],
            key_risks=confidence_data["key_risks"],
            data_sources_used=data_sources_used,
            data_completeness=confidence_data["breakdown"]["data_completeness"],
            model_agreement=confidence_data["breakdown"]["model_agreement"],
            score_matrix=self.poisson.predict_score_matrix().tolist(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        return prediction
    
    def _run_poisson_model(self, home_features: Dict, away_features: Dict) -> Dict:
        """Run modified Dixon-Coles Poisson model"""
        home_goals = home_features.get("goals_scored_avg", 1.2)
        home_conceded = home_features.get("goals_conceded_avg", 1.2)
        away_goals = away_features.get("goals_scored_avg", 1.2)
        away_conceded = away_features.get("goals_conceded_avg", 1.2)
        
        home_xg = home_features.get("xg_for_avg", 0)
        away_xg = away_features.get("xg_for_avg", 0)
        
        if home_xg > 0 and away_xg > 0:
            adjusted_home = 0.6 * home_xg + 0.4 * home_goals
            adjusted_away = 0.6 * away_xg + 0.4 * away_goals
        else:
            adjusted_home = home_goals
            adjusted_away = away_goals
        
        self.poisson.fit(adjusted_home, adjusted_away, home_conceded, away_conceded)
        
        matrix = self.poisson.predict_score_matrix()
        result_probs = self.poisson.get_result_probs(matrix)
        
        result_probs["expected_home"] = adjusted_home
        result_probs["expected_away"] = adjusted_away
        
        return result_probs
    
    def _calculate_btts_prob(self, home_features: Dict, away_features: Dict) -> float:
        """Calculate BTTS probability"""
        home_btts = home_features.get("btts_rate", 0.5)
        away_btts = away_features.get("btts_rate", 0.5)
        return (home_btts + away_btts) / 2
    
    def _generate_recommendation(self, probs: Dict, goal_probs: Dict, confidence: Dict) -> Dict:
        """Generate recommended market and pick"""
        max_prob = max(probs["home"], probs["draw"], probs["away"])
        
        if max_prob == probs["home"]:
            return {"market": "1X2", "pick": "Home Win"}
        elif max_prob == probs["away"]:
            return {"market": "1X2", "pick": "Away Win"}
        else:
            return {"market": "1X2", "pick": "Draw"}
    
    def _generate_explanation(self, fixture: Fixture, home_features: Dict, away_features: Dict, probs: Dict) -> Dict:
        """Generate explanation for prediction"""
        home_team = self.db.query(fixture.home_team).first()
        away_team = self.db.query(fixture.away_team).first()
        
        home_name = home_team.name if home_team else "Home"
        away_name = away_team.name if away_team else "Away"
        
        if probs["home"] >= max(probs["draw"], probs["away"]):
            primary = "{} favored at home".format(home_name)
            why_not_home = ""
            why_not_draw = "Draw unlikely"
            why_not_away = "Away team weak"
        elif probs["away"] >= max(probs["home"], probs["draw"]):
            primary = "{} favored away".format(away_name)
            why_not_home = "Home team weak"
            why_not_draw = "Draw unlikely"
            why_not_away = ""
        else:
            primary = "Close match expected"
            why_not_home = "Evenly matched"
            why_not_draw = ""
            why_not_away = "Competitive"
        
        return {
            "primary_reason": primary,
            "why_not_home": why_not_home,
            "why_not_draw": why_not_draw,
            "why_not_away": why_not_away,
        }
