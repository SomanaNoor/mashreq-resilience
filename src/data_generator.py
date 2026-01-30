
import json
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker
fake = Faker()

# Configuration
OUTPUT_DIR = "./data"

class SyntheticDataGenerator:
    def __init__(self):
        self.customers = self._generate_customers(100)

    def _generate_customers(self, count):
        """Generate consistent customer profiles."""
        print(f"Generating {count} customer profiles...")
        customers = []
        for _ in range(count):
            customers.append({
                "user_id": str(uuid.uuid4())[:8],
                "name": fake.name(),
                "tier": random.choice(["Standard", "Gold", "Platinum", "Private Banking"])
            })
        return customers

    def create_event(self, timestamp, source, content, user=None, latency=None):
        """Helper to create a standard event structure."""
        if not user:
            user = random.choice(self.customers)
        
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "source": source,
            "user_id": user['user_id'],
            "user_tier": user['tier'],
            "content": content,
            "metadata": {
                "latency_ms": latency if latency else random.randint(20, 100),
                "device": random.choice(["iOS", "Android", "Web"]),
                "ip_address": fake.ipv4()
            }
        }

    def generate_noise(self, start_time, duration_minutes, count=50):
        """Generates random background noise events."""
        events = []
        for _ in range(count):
            offset = random.randint(0, duration_minutes * 60)
            ts = start_time + timedelta(seconds=offset)
            
            topics = [
                ("Support Ticket", "I forgot my password"),
                ("App Log", "User logged in successfully"),
                ("ATM Log", "Cash withdrawal successful"),
                ("Support Ticket", "What are the branch hours?"),
                ("Tweet", "Just got my new card, looks great!")
            ]
            source, topic = random.choice(topics)
            events.append(self.create_event(ts, source, f"{topic} - {fake.sentence()}"))
        return events

    def generate_liquidity_story(self):
        """
        NARRATIVE A: Liquidity Rumor
        1. Influencer Tweet (T-30m)
        2. Panic Reaction (10 tickets)
        """
        print("Creating Narrative: Liquidity Rumor...")
        events = []
        base_time = datetime.now() - timedelta(minutes=45)
        
        # 1. The Trigger
        influencer_ts = base_time + timedelta(minutes=15)
        events.append(self.create_event(
            influencer_ts, 
            "Tweet", 
            "⚠️ BREAKING: Hearing rumors that Mashreq ATMs are running empty across Dubai. #BankRun #Mashreq",
            user={"user_id": "INFL_99", "name": "CryptoKing_DXB", "tier": "Influencer"}
        ))
        
        # 2. The Reaction (10 Tickets)
        for i in range(10):
            offset = 16 + i # Minutes after base time (1 min after tweet starts)
            ts = base_time + timedelta(minutes=offset, seconds=random.randint(0, 59))
            
            phrases = [
                "Is my money safe?",
                "I saw a tweet saying you have no cash.",
                "Why can't I withdraw 50k right now?",
                "Are you insolvent?",
                "I want to close my account immediately."
            ]
            events.append(self.create_event(ts, "Support Ticket", random.choice(phrases), latency=random.randint(50, 200)))

        # 3. Add Noise
        noise = self.generate_noise(base_time, 45, count=40)
        
        # Combine and Sort
        full_stream = sorted(events + noise, key=lambda x: x['timestamp'])
        return full_stream

    def generate_cloud_outage_story(self):
        """
        NARRATIVE B: Cloud Outage
        1. Latency Spike (T-20m)
        2. 500 Errors Flood (T-15m)
        3. News Trigger (T-5m)
        """
        print("Creating Narrative: Cloud Outage...")
        events = []
        base_time = datetime.now() - timedelta(minutes=30)
        
        # 1. Latency Warning
        for i in range(5):
            ts = base_time + timedelta(minutes=5, seconds=i*30)
            events.append(self.create_event(ts, "App Log", "API Warning: High Latency detected", latency=random.randint(800, 1500)))

        # 2. The Crash (500 Errors)
        for i in range(30):
            ts = base_time + timedelta(minutes=10, seconds=random.randint(0, 300))
            events.append(self.create_event(
                ts, "App Log", 
                "CRITICAL: 500 Internal Server Error - Gateway Timeout upstream", 
                latency=random.randint(3000, 5000)
            ))

        # 3. The Headline
        news_ts = base_time + timedelta(minutes=25)
        events.append(self.create_event(
            news_ts, "News Feed", 
            "ALERT: Major fire reported at regional AWS Data Center in Bahrain. Banking services expected to be impacted.",
            user={"user_id": "NEWS_BOT", "name": "Global News Wire", "tier": "System"}
        ))

        # 4. Add Noise
        noise = self.generate_noise(base_time, 30, count=20)
        
        full_stream = sorted(events + noise, key=lambda x: x['timestamp'])
        return full_stream

    def save_to_file(self, data, filename):
        with open(f"{OUTPUT_DIR}/{filename}", 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(data)} records to {filename}")

if __name__ == "__main__":
    gen = SyntheticDataGenerator()
    
    # Generate Narratives
    gen.save_to_file(gen.generate_liquidity_story(), "scenario_story_liquidity.json")
    gen.save_to_file(gen.generate_cloud_outage_story(), "scenario_story_cloud_outage.json")
    
    # Generate Baseline for reference
    gen.save_to_file(gen.generate_noise(datetime.now(), 60), "scenario_baseline_noise.json")
    
    print("\n✅ Narrative Scenarios Generated!")
