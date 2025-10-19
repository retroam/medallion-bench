MedallionBench Implementation Guide
Executive Summary
MedallionBench is an evaluation framework that tests LLM agents' ability to compete in the Numerai tournament - a real-world machine learning competition where participants predict stock market movements. The benchmark operates in two modes: (1) a simulated tournament using historical data for rapid iteration and testing, and (2) live tournament participation with real predictions and stakes.
The evaluation tests critical capabilities including model development, risk management, staking decisions, and long-horizon coherence over extended periods (40+ rounds spanning months of tournament participation).
Core Architecture Overview
System Components
MedallionBench/
├── Tournament Environment
│   ├── Simulated Mode (historical rounds 200-400)
│   └── Live Mode (current tournament rounds)
├── Agent System
│   ├── Main Coordinator Agent
│   ├── Data Analysis Sub-agent
│   ├── Model Development Sub-agent
│   └── Risk Management Sub-agent
├── Evaluation Framework
│   ├── Performance Scoring
│   ├── Coherence Testing
│   └── Failure Detection
└── Data Pipeline
    ├── Historical Data Loader
    ├── Live Data Fetcher
    └── Prediction Validator

Implementation Phases
Phase 1: Core Tournament Simulation (Weeks 1-3)
Goal: Build a working simulated tournament that can evaluate agents using historical Numerai data.
1.1 Data Pipeline Setup
class NumeraiDataPipeline:
    """
    Handles all data operations for the tournament.
    
    Requirements:
    - Download historical tournament data (rounds 200-400)
    - Separate features, targets, and eras properly
    - Implement train/validation/live splits per round
    - Cache data locally for efficiency
    """
    
    def __init__(self):
        self.numerapi_client = numerapi.NumerAPI()
        self.cache_dir = "./numerai_cache"
        
    def get_round_data(self, round_num: int) -> Dict:
        """
        Returns data as it would have appeared in that historical round:
        - training: All data up to round_num - 4 (with targets)
        - validation: Recent eras with targets for testing
        - tournament: Current round data WITHOUT targets
        """
        # Implementation required
        pass

Key Implementation Notes:
Use numerapi library to download official data
Each round's data must be split to simulate what was available at that time
Tournament data must have targets removed (agent shouldn't see the future)
Cache everything - downloads are large (>1GB)
1.2 Tournament Environment
class SimulatedNumeraiTournament:
    """
    Simulates the Numerai tournament experience using historical data.
    
    Key mechanics:
    - 4 overlapping rounds at any time
    - Rounds resolve after ~4 weeks (20 rounds)
    - Correlation scores range from -0.25 to +0.25
    - Payouts = stake * (corr_weight * correlation + mmc_weight * mmc)
    """
    
    def __init__(self, start_round=200):
        self.current_round = start_round
        self.agent_balance = 100.0  # Starting NMR
        self.pending_rounds = []  # Rounds awaiting resolution
        self.resolved_rounds = []  # Historical results
        
    def run_round(self, agent):
        # 1. Provide data to agent
        round_data = self.data_pipeline.get_round_data(self.current_round)
        
        # 2. Agent develops model and makes predictions
        predictions = agent.generate_predictions(round_data)
        
        # 3. Agent decides staking
        stake_decision = agent.decide_stake(self.get_agent_context())
        
        # 4. Calculate correlation against hidden targets
        actual_correlation = self.calculate_correlation(
            predictions, 
            self.get_hidden_targets(self.current_round)
        )
        
        # 5. Queue round for delayed resolution
        self.pending_rounds.append({
            'round': self.current_round,
            'stake': stake_decision.amount,
            'correlation': actual_correlation,
            'resolves_at': self.current_round + 20
        })
        
        # 6. Process any resolved rounds
        self.process_resolutions()
        
        # 7. Check failure conditions
        if self.agent_balance <= 0:
            return "BANKRUPTCY"
            
        self.current_round += 1

Critical Details:
Correlation calculation must use Numerai's specific method (Spearman correlation on ranked predictions)
MMC (Meta Model Contribution) is complex - for MVP, use simplified version or historical MMC data
Implement proper 4-week delay for round resolution
Track pending stakes and payouts accurately
1.3 Basic Agent Interface
class NumeraiAgent:
    """
    Base interface that all agents must implement.
    """
    
    @abstractmethod
    async def generate_predictions(self, round_data: Dict) -> pd.DataFrame:
        """
        Generate predictions for all rows in tournament data.
        Returns DataFrame with 'id' and 'prediction' columns.
        """
        pass
        
    @abstractmethod
    async def decide_stake(self, context: Dict) -> StakeDecision:
        """
        Decide how much NMR to stake and on what metrics.
        Context includes balance, recent performance, confidence.
        """
        pass

Phase 2: Failure Modes and Challenges (Week 4)
Goal: Implement realistic failure scenarios that test agent robustness.
2.1 Market Regime Changes
class RegimeManager:
    """
    Simulates different market regimes that affect model performance.
    Based on real Numerai history (e.g., 2021 regime change).
    """
    
    def __init__(self):
        self.regimes = {
            'bull_market': {'corr_multiplier': 1.2, 'volatility': 0.02},
            'bear_market': {'corr_multiplier': 0.8, 'volatility': 0.04},
            'regime_change': {'corr_multiplier': -0.5, 'volatility': 0.08},
            'neutral': {'corr_multiplier': 1.0, 'volatility': 0.03}
        }
        
    def apply_regime_effects(self, base_correlation: float, round_num: int):
        # Implement regime transitions based on historical patterns
        if round_num in [250, 251, 252]:  # Example regime change
            return base_correlation * self.regimes['regime_change']['corr_multiplier']

2.2 Burn Periods
class BurnPeriodSimulator:
    """
    Simulates extended negative correlation periods.
    Critical for testing if agents can survive and recover.
    """
    
    def inject_burn(self, round_num: int, base_correlation: float):
        # Historical burn periods from Numerai
        burn_periods = [
            (210, 215),  # 5-round burn
            (287, 294),  # 7-round burn
        ]
        
        for start, end in burn_periods:
            if start <= round_num <= end:
                # Force negative correlation
                return min(base_correlation - 0.08, -0.02)
        
        return base_correlation

2.3 Feature Importance Drift
class FeatureDrift:
    """
    Simulates changing feature importance over time.
    Tests if agents can adapt their models.
    """
    
    def apply_drift(self, round_num: int, feature_importances: Dict):
        drift_schedule = {
            220: "neutralize_top_10_features",
            260: "inverse_importance_weights",
            300: "introduce_new_feature_set"
        }
        
        if round_num in drift_schedule:
            return self.apply_drift_type(
                feature_importances, 
                drift_schedule[round_num]
            )

Phase 3: Long-Horizon Coherence Testing (Week 5)
Goal: Test agent's ability to maintain coherent strategy over 40+ rounds.
3.1 Memory and Consistency Challenges
class CoherenceEvaluator:
    """
    Tests agent's long-term memory and strategic consistency.
    """
    
    def __init__(self):
        self.checkpoints = {}
        self.strategy_history = []
        
    def create_checkpoint(self, agent, round_num):
        """Store agent's current strategy and beliefs"""
        self.checkpoints[round_num] = {
            'stated_strategy': agent.explain_strategy(),
            'feature_weights': agent.get_feature_importance(),
            'risk_tolerance': agent.get_risk_parameters(),
            'recent_decisions': agent.get_recent_decisions()
        }
        
    def test_consistency(self, agent, current_round):
        """Test if agent maintains consistent strategy"""
        
        tests = []
        
        # Test 1: Can agent recall early decisions?
        if current_round == 40:
            tests.append({
                'question': "What features did you prioritize in round 5?",
                'expected': self.checkpoints[5]['feature_weights']
            })
            
        # Test 2: Can agent explain strategy evolution?
        if current_round == 60:
            tests.append({
                'question': "How has your strategy changed since round 20?",
                'evaluate': 'coherent_explanation'
            })
            
        # Test 3: Does agent remember failure causes?
        if current_round == 80:
            tests.append({
                'question': "Why did your model fail in rounds 31-35?",
                'evaluate': 'accurate_recall'
            })
            
        return tests

3.2 Staking Consistency Evaluation
class StakingCoherenceTest:
    """
    Specifically tests coherence in staking decisions.
    """
    
    def evaluate_staking_evolution(self, stake_history):
        metrics = {
            'consistency': self.calculate_stake_consistency(stake_history),
            'panic_events': self.detect_panic_staking(stake_history),
            'overleveraging': self.detect_overleveraging(stake_history),
            'strategy_drift': self.measure_strategy_drift(stake_history)
        }
        
        # Flag incoherent patterns
        if metrics['panic_events'] > 2:
            return "FAILURE: Panic staking detected"
        
        if metrics['strategy_drift'] > 0.7:
            return "FAILURE: Inconsistent staking strategy"

Phase 4: Live Tournament Integration (Week 6)
Goal: Enable real tournament participation with safety measures.
4.1 Live Data Interface
class LiveTournamentInterface:
    """
    Handles interaction with live Numerai tournament.
    """
    
    def __init__(self):
        self.napi = numerapi.NumerAPI()
        self.current_round = self.napi.get_current_round()
        
    def prepare_live_submission(self, agent):
        # Download latest data
        live_data = self.napi.download_dataset("v4.3/live.parquet")
        
        # Agent generates predictions
        predictions = agent.generate_predictions(live_data)
        
        # Validate predictions
        validation = self.validate_predictions(predictions, live_data)
        if not validation.is_valid:
            return f"ERROR: {validation.errors}"
            
        # Get stake recommendation with safety limits
        stake = agent.decide_stake(self.get_live_context())
        safe_stake = self.apply_safety_limits(stake)
        
        # Prepare submission package
        return {
            'predictions_file': self.save_predictions(predictions),
            'stake_amount': safe_stake.amount,
            'stake_config': safe_stake.multipliers,
            'validation_report': validation,
            'requires_human_review': safe_stake.amount > 10.0
        }

4.2 Safety Mechanisms
class SafetyController:
    """
    Prevents catastrophic failures in live mode.
    """
    
    def __init__(self):
        self.max_stake_percentage = 0.10  # Max 10% of balance
        self.max_absolute_stake = 50.0    # Max 50 NMR per round
        self.require_simulation_pass = True
        self.min_confidence_threshold = 0.6
        
    def validate_stake(self, stake_decision, context):
        validations = []
        
        # Check percentage limit
        if stake_decision.amount > context['balance'] * self.max_stake_percentage:
            stake_decision.amount = context['balance'] * self.max_stake_percentage
            validations.append("Reduced stake to 10% of balance")
            
        # Check absolute limit
        if stake_decision.amount > self.max_absolute_stake:
            stake_decision.amount = self.max_absolute_stake
            validations.append(f"Capped at {self.max_absolute_stake} NMR")
            
        # Check confidence
        if context['confidence'] < self.min_confidence_threshold:
            stake_decision.amount *= 0.5
            validations.append("Halved stake due to low confidence")
            
        return stake_decision, validations

Phase 5: Scoring and Evaluation (Week 7)
5.1 Multi-Dimensional Scoring
class MedallionScorer:
    """
    Comprehensive scoring across multiple dimensions.
    """
    
    def calculate_score(self, agent_run):
        scores = {
            # Performance (30%)
            'performance': {
                'total_return': self.calculate_return(agent_run),
                'sharpe_ratio': self.calculate_sharpe(agent_run),
                'max_drawdown': self.calculate_max_drawdown(agent_run),
                'weight': 0.30
            },
            
            # Staking Intelligence (25%)
            'staking': {
                'kelly_adherence': self.evaluate_kelly_criterion(agent_run),
                'risk_management': self.evaluate_risk_management(agent_run),
                'consistency': self.evaluate_stake_consistency(agent_run),
                'weight': 0.25
            },
            
            # Model Quality (20%)
            'modeling': {
                'prediction_quality': self.evaluate_predictions(agent_run),
                'feature_engineering': self.evaluate_features(agent_run),
                'adaptation': self.evaluate_adaptation(agent_run),
                'weight': 0.20
            },
            
            # Coherence (25%)
            'coherence': {
                'memory_tests': self.evaluate_memory(agent_run),
                'strategy_consistency': self.evaluate_strategy(agent_run),
                'failure_recovery': self.evaluate_recovery(agent_run),
                'weight': 0.25
            }
        }
        
        return self.compute_weighted_score(scores)

Testing Strategy
Unit Tests Required
Data Pipeline Tests
Verify correct train/validation/tournament splits
Ensure targets are properly hidden
Test era handling
Correlation Calculation Tests
Match Numerai's exact correlation method
Handle edge cases (all same predictions, etc.)
Staking Mechanism Tests
Verify payout calculations
Test bankruptcy conditions
Validate stake limits
Coherence Tests
Verify memory checkpoint system
Test question generation
Validate consistency metrics
Integration Tests Required
Full Tournament Simulation
Run 100-round simulation
Verify no data leakage
Check performance metrics
Failure Mode Tests
Inject each failure type
Verify agent handling
Check recovery detection
Live Mode Tests (with test account)
Test prediction generation
Verify safety limits
Check submission format
Performance Requirements
Simulation Speed: Must complete 100 rounds in <1 hour
Memory Usage: <8GB RAM for full historical data
Data Caching: All historical data cached locally
Concurrent Rounds: Track 4 overlapping rounds correctly
Scoring Latency: Full scoring in <30 seconds per round
Critical Implementation Notes
Data Integrity
No future data leakage: Agent must never see targets for rounds it's predicting
Proper era handling: Numerai's eras are time-based, not random
Feature alignment: Features change over time - handle versioning
Realism
Correlation variance: Real correlations have high variance (std ~0.03)
Delayed feedback: 4-week delay is crucial for realism
Overlapping rounds: Always 4 rounds pending in real tournament
Agent Interface
Async operations: Agents may take time to train models
Tool access: Agents need tools for data analysis, model training
Memory systems: Agents need persistent memory across rounds
Safety
Stake limits: Prevent agents from betting entire bankroll
Human review: Require review for large stakes
Simulation gate: Must pass simulation before live mode
Delivery Milestones
Week 1-3: MVP Simulation
Working tournament simulation with historical data
Basic agent interface
Simple scoring
Week 4-5: Failure Modes & Coherence
Regime changes, burns, drift
Coherence testing
Advanced scoring
Week 6-7: Live Mode & Polish
Live tournament interface
Safety mechanisms
Complete documentation
Dependencies
# Required packages
numerapi >= 2.18.0       # Official Numerai API
pandas >= 1.5.0          # Data manipulation
numpy >= 1.23.0          # Numerical operations
scikit-learn >= 1.2.0    # Correlation calculations
inspect-ai >= 0.3.0      # Evaluation framework
asyncio                  # Async agent operations

Success Criteria
The implementation is complete when:
Simulation Mode
Can run 100+ historical rounds
Produces consistent, reproducible results
All failure modes implemented
Live Mode
Successfully generates valid predictions
Applies safety limits correctly
Produces human-readable submission package
Scoring
Accurately measures all dimensions
Produces interpretable results
Identifies agent failure modes
Testing
90%+ test coverage
All integration tests passing
Performance benchmarks met
Questions for Product Team
Historical Data Range: Which rounds should we use? (Recommended: 200-400)
Maximum Stake Limits: What's the maximum real NMR we're willing to risk?
Human Review Threshold: At what stake level require human review?
Scoring Weights: Adjust the weight balance between performance/coherence/etc?
Failure Thresholds: When should we terminate an agent run?

This implementation guide provides the complete blueprint for building MedallionBench. The engineer should start with Phase 1 (simulation) and progressively add complexity. The most critical aspects are data integrity (no leakage) and realistic tournament mechanics (proper correlation calculation, stake resolution, and timing).

