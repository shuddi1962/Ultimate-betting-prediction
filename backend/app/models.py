from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class League(Base):
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    country = Column(String(100))
    api_football_id = Column(Integer, unique=True, nullable=True)
    sportmonks_id = Column(Integer, nullable=True)
    season_year = Column(Integer)
    is_tracked = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow())
    updated_at = Column(DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    short_name = Column(String(50))
    api_football_id = Column(Integer, unique=True, nullable=True)
    sportmonks_id = Column(Integer, nullable=True)
    transfermarkt_id = Column(Integer, nullable=True)
    sofascore_id = Column(Integer, nullable=True)
    fotmob_id = Column(Integer, nullable=True)
    fbref_slug = Column(String(300), nullable=True)
    elo_rating = Column(Float, default=1500.0)
    elo_attack = Column(Float, default=1500.0)
    elo_defense = Column(Float, default=1500.0)
    updated_at = Column(DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())
    
    fixtures_home = relationship("Fixture", foreign_keys="Fixture.home_team_id", back_populates="home_team")
    fixtures_away = relationship("Fixture", foreign_keys="Fixture.away_team_id", back_populates="away_team")
    xg_history = relationship("TeamXGHistory", back_populates="team")
    injuries = relationship("Injury", back_populates="team")
    elo_history = relationship("EloHistory", back_populates="team")


class Fixture(Base):
    __tablename__ = "fixtures"
    
    id = Column(Integer, primary_key=True)
    api_football_id = Column(Integer, unique=True, nullable=True)
    sportmonks_id = Column(Integer, nullable=True)
    sofascore_id = Column(String(100), nullable=True)
    fotmob_id = Column(String(100), nullable=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    kickoff_utc = Column(DateTime, nullable=False)
    status = Column(String(50), default='NS')
    home_score = Column(Integer)
    away_score = Column(Integer)
    ht_home_score = Column(Integer)
    ht_away_score = Column(Integer)
    venue = Column(String(200))
    referee = Column(String(200))
    data_sources_used = Column(ARRAY(String))
    last_updated = Column(DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())
    
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="fixtures_home")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="fixtures_away")
    league = relationship("League")
    statistics = relationship("MatchStatistics", back_populates="fixture")
    prediction = relationship("Prediction", back_populates="fixture", uselist=False)


class MatchStatistics(Base):
    __tablename__ = "match_statistics"
    
    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    is_home = Column(Boolean)
    shots_total = Column(Integer)
    shots_on_target = Column(Integer)
    shots_off_target = Column(Integer)
    shots_blocked = Column(Integer)
    possession_pct = Column(Float)
    corners = Column(Integer)
    fouls = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    xg = Column(Float)
    dangerous_attacks = Column(Integer)
    big_chances = Column(Integer)
    passes_total = Column(Integer)
    passes_accurate = Column(Integer)
    offsides = Column(Integer)
    saves = Column(Integer)
    goal_kicks = Column(Integer)
    throw_ins = Column(Integer)
    recorded_at = Column(DateTime, default=datetime.utcnow())
    is_final = Column(Boolean, default=False)
    data_source = Column(String(50))
    
    fixture = relationship("Fixture", back_populates="statistics")
    team = relationship("Team")


class TeamXGHistory(Base):
    __tablename__ = "team_xg_history"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=True)
    xg_for = Column(Float)
    xg_against = Column(Float)
    npxg_for = Column(Float)
    npxg_against = Column(Float)
    goals_scored = Column(Integer)
    goals_conceded = Column(Integer)
    xg_overperformance = Column(Float)
    source = Column(String(50))
    match_date = Column(DateTime)
    season_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow())
    
    team = relationship("Team", back_populates="xg_history")


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), unique=True)
    home_win_prob = Column(Float)
    draw_prob = Column(Float)
    away_win_prob = Column(Float)
    expected_home_goals = Column(Float)
    expected_away_goals = Column(Float)
    expected_total_goals = Column(Float)
    btts_yes_prob = Column(Float)
    over_2_5_prob = Column(Float)
    over_1_5_prob = Column(Float)
    over_3_5_prob = Column(Float)
    recommended_market = Column(String(200))
    recommended_pick = Column(String(200))
    confidence_score = Column(Float)
    primary_reason = Column(Text)
    why_not_home = Column(Text)
    why_not_draw = Column(Text)
    why_not_away = Column(Text)
    key_risks = Column(ARRAY(String))
    injuries_impact = Column(Text)
    data_sources_used = Column(ARRAY(String))
    data_completeness = Column(Float)
    model_agreement = Column(Float)
    poisson_home_goals = Column(Float)
    poisson_away_goals = Column(Float)
    score_matrix = Column(JSONB)
    all_markets = Column(JSONB)
    actual_result = Column(String(10))
    prediction_correct = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow())
    updated_at = Column(DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())
    
    fixture = relationship("Fixture", back_populates="prediction")


class Injury(Base):
    __tablename__ = "injuries"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_name = Column(String(200))
    position = Column(String(50))
    injury_type = Column(String(200))
    injured_since = Column(DateTime)
    expected_return = Column(DateTime)
    is_suspended = Column(Boolean, default=False)
    market_value_eur = Column(Float)
    source = Column(String(50))
    scraped_at = Column(DateTime, default=datetime.utcnow())
    
    team = relationship("Team", back_populates="injuries")


class EloHistory(Base):
    __tablename__ = "elo_history"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=True)
    elo_before = Column(Float)
    elo_after = Column(Float)
    elo_change = Column(Float)
    match_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow())
    
    team = relationship("Team", back_populates="elo_history")


Index("idx_fixtures_kickoff", Fixture.kickoff_utc)
Index("idx_fixtures_status", Fixture.status)
Index("idx_team_xg_team_date", TeamXGHistory.team_id, TeamXGHistory.match_date.desc())
Index("idx_predictions_fixture", Prediction.fixture_id)
Index("idx_match_stats_fixture", MatchStatistics.fixture_id)
