from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models import Fixture, TeamXGHistory, Injury


class ConfidenceCalculator:
    """Calculate prediction confidence based on data quality and model agreement"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_confidence(self, fixture: Fixture, 
                            home_features: Dict, away_features: Dict,
                            model_probs: Dict[str, float],
                            data_sources_used: List[str]) -> Dict:
        """Calculate overall confidence score and breakdown"""
        
        breakdowns = {}
        
        breakdowns["data_completeness"] = self._calculate_data_completeness(
            fixture, data_sources_used
        )
        
        breakdowns["model_agreement"] = self._calculate_model_agreement(model_probs)
        
        breakdowns["sample_size"] = self._calculate_sample_size_confidence(
            fixture.home_team_id, fixture.away_team_id
        )
        
        breakdowns["injury_certainty"] = self._calculate_injury_certainty(
            fixture.home_team_id, fixture.away_team_id, fixture.kickoff_utc
        )
        
        breakdowns["xg_data_available"] = self._calculate_xg_confidence(home_features, away_features)
        
        breakdowns["h2h_sample"] = self._calculate_h2h_confidence(
            fixture.home_team_id, fixture.away_team_id
        )
        
        overall = (
            0.25 * breakdowns["data_completeness"] +
            0.25 * breakdowns["model_agreement"] +
            0.20 * breakdowns["sample_size"] +
            0.15 * breakdowns["injury_certainty"] +
            0.10 * breakdowns["xg_data_available"] +
            0.05 * breakdowns["h2h_sample"]
        )
        
        uncertainties = []
        if breakdowns["injury_certainty"] < 0.7:
            uncertainties.append("Injury status uncertain for one or both teams")
        if breakdowns["sample_size"] < 0.6:
            uncertainties.append(f"Limited historical data (fewer than 8 matches for one team)")
        if breakdowns["xg_data_available"] < 0.5:
            uncertainties.append("xG data unavailable - using goals-based prediction only")
        if breakdowns["h2h_sample"] < 0.5:
            uncertainties.append("Limited H2H history between these teams")
        
        return {
            "overall_confidence": round(overall, 2),
            "breakdown": {k: round(v, 2) for k, v in breakdowns.items()},
            "key_uncertainties": uncertainties,
        }
    
    def _calculate_data_completeness(self, fixture: Fixture, sources: List[str]) -> float:
        """How much data was available from scrapers"""
        expected_sources = ["sofascore", "fotmob", "fbref", "understat", "transfermarkt"]
        sources_lower = [s.lower() for s in sources]
        
        found = sum(1 for s in expected_sources if s in sources_lower)
        return min(1.0, found / len(expected_sources))
    
    def _calculate_model_agreement(self, model_probs: Dict[str, float]) -> float:
        """How much do the models agree?"""
        probs = [model_probs.get("home", 0), model_probs.get("draw", 0), model_probs.get("away", 0)]
        
        max_prob = max(probs)
        entropy = -sum(p * (p and np.log(p) or 0) for p in probs)
        max_entropy = -np.log(1/3)
        
        agreement = 1.0 - (entropy / max_entropy)
        
        if max_prob > 0.65:
            agreement = min(1.0, agreement + 0.2)
        
        return max(0.0, min(1.0, agreement))
    
    def _calculate_sample_size_confidence(self, home_id: int, away_id: int) -> float:
        """Confidence based on number of historical matches"""
        home_matches = (
            self.db.query(TeamXGHistory)
            .filter(TeamXGHistory.team_id == home_id)
            .count()
        )
        away_matches = (
            self.db.query(TeamXGHistory)
            .filter(TeamXGHistory.team_id == away_id)
            .count()
        )
        
        min_matches = min(home_matches, away_matches)
        
        if min_matches >= 20:
            return 1.0
        elif min_matches >= 10:
            return 0.8
        elif min_matches >= 5:
            return 0.6
        else:
            return 0.3
    
    def _calculate_injury_certainty(self, home_id: int, away_id: int, match_date) -> float:
        """How certain are we about player availability"""
        home_injuries = (
            self.db.query(Injury)
            .filter(Injury.team_id == home_id)
            .filter(Injury.expected_return > match_date)
            .count()
        )
        away_injuries = (
            self.db.query(Injury)
            .filter(Injury.team_id == away_id)
            .filter(Injury.expected_return > match_date)
            .count()
        )
        
        total_impact = (home_injuries + away_injuries) * 0.1
        return max(0.0, 1.0 - total_impact)
    
    def _calculate_xg_confidence(self, home_features: Dict, away_features: Dict) -> float:
        """Is xG data available?"""
        home_xg = home_features.get("home_xg_for_avg", 0)
        away_xg = away_features.get("away_xg_for_avg", 0)
        
        if home_xg > 0 and away_xg > 0:
            return 1.0
        elif home_xg > 0 or away_xg > 0:
            return 0.5
        else:
            return 0.0
    
    def _calculate_h2h_confidence(self, home_id: int, away_id: int) -> float:
        """How many H2H meetings are available"""
        from app.models import Fixture as F
        h2h_count = (
            self.db.query(F)
            .filter(
                ((F.home_team_id == home_id) & (F.away_team_id == away_id)) |
                ((F.home_team_id == away_id) & (F.away_team_id == home_id))
            )
            .count()
        )
        
        if h2h_count >= 10:
            return 1.0
        elif h2h_count >= 5:
            return 0.6
        else:
            return 0.3


import numpy as np
