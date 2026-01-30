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
        Runs the simulation.
        
        Variables are normalized to contribute to a 'Total Impact Score' (0-100+).
        Each variable has a weight and a scaling factor.
        """
        
        # 1. Define Mean & Sigma (Noise) for inputs to simulate uncertainty
        # We assume 10% standard deviation variance in the realization of these risks
        
        # Generate random distributions
        rng = np.random.default_rng()
        
        sim_rates = rng.normal(interest_rate_bps, interest_rate_bps * 0.1 + 1, self.iterations)
        sim_downtime = rng.normal(downtime_minutes, downtime_minutes * 0.1 + 1, self.iterations)
        sim_fines = rng.normal(regulatory_fine_mm, regulatory_fine_mm * 0.1 + 0.1, self.iterations)
        sim_vix = rng.normal(market_volatility_vix, market_volatility_vix * 0.1 + 1, self.iterations)
        sim_cyber = rng.normal(cyber_breach_cost_mm, cyber_breach_cost_mm * 0.1 + 0.1, self.iterations)
        
        # 2. Calculate Impact Contributions (Normalized to partial scores)
        
        # Interest Rate (bps): >200bps is high stress. Max 500. Weight 15.
        score_rates = (sim_rates / 500) * 15
        
        # Downtime (min): >240min (4hr) is critical. Max 1440. Weight 30 (Operational is key).
        score_downtime = (sim_downtime / 480) * 30 
        
        # Reg Fines ($MM): >50MM is huge. Weight 20.
        score_fines = (sim_fines / 50) * 20
        
        # VIX: >30 is panic. Max 100. Weight 10.
        score_vix = (sim_vix / 50) * 10
        
        # Cyber Cost ($MM): >10MM is severe. Weight 25.
        score_cyber = (sim_cyber / 20) * 25
        
        # 3. Total Impact Score
        total_impact = score_rates + score_downtime + score_fines + score_vix + score_cyber
        
        # Clip negative values (distributions can go negative if mean is near 0)
        total_impact = np.maximum(total_impact, 0)
        
        # 4. Analyze Results
        breach_count = np.sum(total_impact > self.impact_tolerance)
        breach_prob = (breach_count / self.iterations) * 100
        
        mean_impact = np.mean(total_impact)
        var_95 = np.percentile(total_impact, 95)
        
        return {
            "simulation_data": total_impact,
            "breach_probability": breach_prob,
            "mean_impact": mean_impact,
            "var_95": var_95,
            "is_breach": breach_prob > 5.0 # If >5% probability of failure, it's a Breach Scenario
        }

if __name__ == "__main__":
    # Test
    sim = SimulationEngine()
    res = sim.run_simulation(100, 60, 0, 20, 0)
    print(f"Normal Scenario Breach Prob: {res['breach_probability']:.2f}%")
    
    res_stress = sim.run_simulation(400, 300, 20, 50, 10)
    print(f"Stress Scenario Breach Prob: {res_stress['breach_probability']:.2f}%")
