import numpy as np
import pandas as pd

class SimulationEngine:
    """
    Monte Carlo Simulation Engine for Operational Resilience.
    Models the probability of breaching Impact Tolerance based on 5 key stress variables.
    """
    
    def __init__(self, iterations=5000, impact_tolerance=80):
        self.iterations = iterations
        self.impact_tolerance = impact_tolerance
        
    def run_simulation(self, 
                      interest_rate_bps: int, 
                      downtime_minutes: int, 
                      regulatory_fine_mm: float, 
                      market_volatility_vix: float, 
                      cyber_breach_cost_mm: float) -> dict:
        """
        Runs the simulation to estimate Financial Loss ($MM).
        
        Model Assumptions:
        - Downtime Cost: ~$50k per hour ($0.83k/min) for digital banking channels
        - Regulatory Fines: As input (+ uncertainty)
        - Cyber Cost: As input (+ uncertainty)
        - Market Severity: Multiplier effect on liquidity costs
        """
        
        # Generator
        rng = np.random.default_rng()
        
        # 1. Simulate Uncertainty (Distributions)
        # We model "fat tails" (extreme events) using wider variance for Cyber & Fines
        
        # Downtime: Standard distribution (+/- 20%)
        sim_downtime = rng.normal(downtime_minutes, downtime_minutes * 0.2, self.iterations)
        
        # Fines: Log-normal (skewed towards higher fines)
        # Using simple normal for stability but with high variance
        sim_fines = rng.normal(regulatory_fine_mm, regulatory_fine_mm * 0.3 + 0.1, self.iterations)
        
        # Cyber: High variance (+/- 40%)
        sim_cyber = rng.normal(cyber_breach_cost_mm, cyber_breach_cost_mm * 0.4 + 0.1, self.iterations)
        
        # 2. Calculate Financial Loss Models ($ Millions)
        
        # A. Downtime Loss ($0.83k/min = $0.00083M/min)
        COST_PER_MIN_MM = 0.00083
        loss_downtime = np.maximum(sim_downtime, 0) * COST_PER_MIN_MM
        
        # B. Direct Costs
        loss_fines = np.maximum(sim_fines, 0)
        loss_cyber = np.maximum(sim_cyber, 0)
        
        # C. Market / Liquidity Impact (Indirect)
        # If VIX > 30 and Rates > 100bps, liquidity costs spike.
        # Simplified: Base 0.1M, multiplier if stressed
        market_stress_factor = (market_volatility_vix / 20) * (interest_rate_bps / 50)
        loss_market = rng.normal(0.1, 0.05, self.iterations) * np.maximum(market_stress_factor, 1.0)
        
        # 3. Total Financial Loss ($MM)
        total_loss_mm = loss_downtime + loss_fines + loss_cyber + loss_market
        
        # Clip at 0
        total_loss_mm = np.maximum(total_loss_mm, 0)
        
        # 4. Analyze Results
        
        # Risk Appetite: $5M for a single operational incident is the tolerance threshold
        RISK_TOLERANCE_MM = 5.0
        
        breach_count = np.sum(total_loss_mm > RISK_TOLERANCE_MM)
        breach_prob = (breach_count / self.iterations) # Decimal, not percentage
        
        mean_loss = np.mean(total_loss_mm)
        var_95 = np.percentile(total_loss_mm, 95) # 95% Confidence Level VaR
        
        return {
            "simulation_data": total_loss_mm,
            "breach_probability": breach_prob,
            "mean_impact": mean_loss, # In $MM
            "var_95": var_95,         # In $MM
            "is_breach": breach_prob > 0.10 # Warning if >10% chance of exceeding tolerance
        }

if __name__ == "__main__":
    # Test
    sim = SimulationEngine()
    res = sim.run_simulation(100, 60, 0, 20, 0)
    print(f"Normal Scenario Breach Prob: {res['breach_probability']:.2f}%")
    
    res_stress = sim.run_simulation(400, 300, 20, 50, 10)
    print(f"Stress Scenario Breach Prob: {res_stress['breach_probability']:.2f}%")
