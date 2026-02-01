"""
Synthetic Social Signals Generator for Mashreq Bank Scenarios
==============================================================
Generates 200 signals across 3 specific scenarios to test:
- Viral Velocity Engine
- Internal Telemetry Shadowing
- Sarcasm Detection & Routing

Scenarios:
1. Digital Dirham Bridge Failure (MISINFORMATION) - 70 signals, 50+ in 10 min
2. Trusted Device Loop (SERVICE) - 60 signals, sarcasm-heavy
3. Security Verification Phishing (FRAUD) - 70 signals, clustered timestamps
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Base timestamp for 2026
BASE_TIME = datetime(2026, 2, 1, 8, 0, 0)

# Platform distribution
PLATFORMS = ['X', 'Reddit', 'Facebook', 'Instagram', 'LinkedIn', 'WhatsApp']
PLATFORM_WEIGHTS = [0.35, 0.20, 0.20, 0.10, 0.05, 0.10]

def get_platform():
    return random.choices(PLATFORMS, weights=PLATFORM_WEIGHTS)[0]

def get_influence_score(is_high_urgency=False):
    """Generate user influence score (1-10)"""
    if is_high_urgency:
        return random.randint(5, 10)
    return random.randint(1, 10)

# =============================================================================
# SCENARIO 1: Digital Dirham Bridge Failure (MISINFORMATION)
# =============================================================================
DIGITAL_DIRHAM_TEMPLATES = [
    # Technical panic jargon
    "BREAKING: Mashreq to Digital Dirham bridge is FAILING. Bridge timeout errors everywhere!",
    "Can't transfer to my CBDC wallet. Ledger sync error on Mashreq side. Anyone else?",
    "Digital Dirham bridge completely down. Central Bank system rejecting all Mashreq connections!",
    "@MashreqBank your CBDC bridge has been timing out for 30 mins. What's happening??",
    "WARNING: Major ledger sync failure between Mashreq and Digital Dirham. Funds not reflecting!",
    "Just tried 5 times - Bridge timeout every single attempt. Is Mashreq insolvent?",
    "CBDC connection lost on Mashreq. Are they having liquidity issues?",
    "My Digital Dirham transfer stuck in limbo. Mashreq bridge showing critical errors.",
    "Ledger sync error 0x4F2A - Any tech people know what this means for our money?",
    "UAE Central Bank Digital Currency bridge to Mashreq is DEAD. Panic time?",
    "Can't move funds to Digital Dirham. Bridge failure message. Is this the end?",
    "URGENT: Digital Dirham conversions failing at Mashreq. Bridge infrastructure collapse?",
    "Mashreq CBDC gateway throwing 'Ledger consensus failure' errors. This is serious!",
    "Anyone getting 'Bridge timeout - retry later' on Digital Dirham transfers? Been hours now.",
    "My salary in Digital Dirham can't be received - Mashreq bridge rejecting all incoming!",
    "Central Bank digital currency bridge to Mashreq banks showing massive failures.",
    "CBDC ledger not syncing with Mashreq. Where is my money going?!",
    "Tried to pay with Digital Dirham via Mashreq - 'Bridge connection terminated' error!",
    "Is the UAE CBDC system collapsing? Mashreq bridge failures point to systemic issues.",
    "Digital Dirham to AED conversion stuck. Mashreq bridge has been down since morning.",
    "Withdrawing everything from Mashreq. Can't trust a bank with CBDC bridge failures.",
    "ALERT: Mashreq Digital Dirham integration is having critical bridge sync issues!",
    "Ledger error, bridge timeout, sync failure - the holy trinity of Mashreq CBDC problems today",
    "If Mashreq can't handle Digital Dirham bridge, maybe time to switch banks?",
    "CBDC bridge failure at Mashreq. This is why I don't trust digital currencies!",
    "Mashreq's Digital Dirham bridge throwing 'ledger desync detected' warnings.",
    "Central Bank Digital Currency timeout on ALL Mashreq transactions. Confirmed!",
    "Bridge failure affecting thousands. Mashreq Digital Dirham completely unusable!",
    "Can someone from @MashreqBank explain the CBDC bridge timeout epidemic?",
    "First the app, now the CBDC bridge. Mashreq infrastructure is crumbling!",
]

# =============================================================================
# SCENARIO 2: Trusted Device Loop (SERVICE + SARCASM)
# =============================================================================
TRUSTED_DEVICE_TEMPLATES = [
    # Frustration + sarcasm
    "Love being locked out of my own money because Mashreq Neo doesn't recognize my phone /s",
    "Day 3 of the 'trusted device' loop. The chatbot tells me to add my device. The app tells me to verify. Infinite loop. 🔄",
    "Oh great, another security update that breaks trusted device recognition. Thanks Mashreq Neo! /s",
    "Mashreq Neo: 'This device is not recognized.' Me: 'It's literally the same phone.' 🤦",
    "Stuck in trusted device verification hell. Chatbot loop #47, still no solution.",
    "The irony of a 'security update' that locks legitimate users out. Well done Mashreq! /s",
    "Can't access Neo app after update. 'Add trusted device' leads to 'verify identity' leads to 'add trusted device'. Circle of misery.",
    "Absolutely LOVE when my biometric that worked yesterday suddenly 'needs reverification' /sarcasm",
    "Mashreq Neo trusted device feature is a joke. My device has been 'trusted' for 2 years!",
    "Security update broke everything. Neo app keeps asking for 2FA on a trusted device. Logic?",
    "Chatbot: 'Have you tried adding your trusted device?' Me: 'For the 100th time, YES!' 😤",
    "Locked out of my account AGAIN. Mashreq Neo 'trusted' device my foot!",
    "The Mashreq Neo chatbot loop is peak comedy. Ask for help → redirect to app → app fails → ask chatbot. Repeat.",
    "Really enjoying not being able to pay my bills because of 'enhanced security' /s",
    "Neo app after security update: Your trusted device isn't trusted anymore. Sorry not sorry.",
    "Whoever designed the trusted device flow at Mashreq Neo clearly never tested it /s",
    "Been stuck in the chatbot → app → chatbot loop for 2 hours. This is my life now.",
    "Mashreq Neo: Making you feel like a fraudster on your own account since the latest update!",
    "The trusted device feature is NOT working after security update. Anyone else or just lucky me? /s",
    "Imagine having to go to a BRANCH to fix digital banking. The future is here, folks! /s",
    "'Device not recognized' on the phone I use EVERY DAY. Make it make sense @MashreqBank",
    "Neo app trust issues are worse than my ex's. At least she recognized my face. 😂",
    "Security update + trusted device bug = locked customers. Math checks out! /s",
    "Chatbot loop count: 12. Blood pressure: Rising. Faith in Mashreq Neo: Plummeting.",
    "If the 'trusted device' feature can't trust my only device, what's the point?",
    "Love the new feature where Neo forgets my device exists after every security patch! /s",
    "3 days, 4 chatbot sessions, 2 call center holds - still can't get past trusted device screen.",
    "Mashreq Neo security update: Now with 100% more lockouts! Order now! /s",
    "The irony of 'trusted device' being the most UNtrustworthy feature in the app 🙃",
    "At this point the trusted device loop is a feature, not a bug. Right Mashreq? /s",
]

# =============================================================================
# SCENARIO 3: Security Verification Phishing Wave (FRAUD)
# =============================================================================
PHISHING_WAVE_TEMPLATES = [
    # Urgent warnings about scam calls
    "⚠️ WARNING: Got a call from 'Mashreq Legal Department' asking for my OTP. SCAM!",
    "BEWARE: Scammers calling from +971-55-XXX-XXXX claiming to be Mashreq Security. They asked for my PIN!",
    "PSA: Mashreq will NEVER ask for your OTP on a call. Just got a fake 'verification call'. Don't fall for it!",
    "Received call from 'Mashreq Security Department' saying my account is compromised. Asked for OTP. Hung up immediately!",
    "SCAM ALERT: Fake Mashreq Legal call asking to 'verify' my identity with OTP. Report this!",
    "Just reported a scam call to police. Person claimed to be from Mashreq Security, wanted my card details.",
    "Warning others: 'Mashreq Legal' call is a SCAM. They sound very convincing but it's fraud!",
    "If you get a call from Mashreq 'Security Verification Team' - IT'S FAKE. They asked for my OTP.",
    "Fraudsters are calling pretending to be Mashreq Legal. DO NOT share any details! Just happened to me.",
    "URGENT: Phishing wave targeting Mashreq customers. Got 3 calls today from fake 'Security Department'.",
    "My elderly mother almost gave her OTP to 'Mashreq Legal' caller. Please warn your families!",
    "Scam call claimed my Mashreq account was used for 'illegal transfer'. Asked for OTP to 'cancel'. DO NOT BELIEVE!",
    "Impersonating Mashreq Legal Department is apparently the new scam. Got called twice today!",
    "+971-4-XXX-XXXX is a SCAM number. Claims to be Mashreq Security. Asked for full card number!",
    "These 'Mashreq Legal' scammers are persistent! Third call this week asking for security details.",
    "PSA: Real Mashreq staff will NEVER call asking for OTP, PIN, or CVV. The fake calls sound real tho!",
    "Just got a 'final warning' call from 'Mashreq Legal' about account suspension. 100% scam!",
    "Reporting this everywhere: Fake Mashreq Security calls asking customers to verify with OTP. It's fraud!",
    "The 'Mashreq Legal Department' scam call even had background call center noise. Very sophisticated!",
    "WARNING: Scammers have Mashreq customers' phone numbers. Getting 'verification' scam calls.",
    "Friends, if 'Mashreq Security' calls asking to verify your identity - hang up! It's a phishing scam!",
    "These fake Mashreq Legal calls need to stop. Just blocked 5 numbers this week!",
    "Scam alert: 'Your Mashreq account is linked to money laundering' - call asking for OTP. Total fraud!",
    "'Mashreq Security Department' caller wanted me to read my OTP to 'secure' my account. Yeah right!",
    "Be careful everyone! Fake Mashreq calls are going around. They ask for OTP claiming fraud prevention!",
    "Just saved my colleague from falling for the 'Mashreq Legal verification' scam. Spread awareness!",
    "The audacity of these scammers calling as 'Mashreq Legal' and asking for PINs! Report them!",
    "FRAUD ALERT: Coordinated scam campaign impersonating Mashreq Security. Don't share ANY details!",
    "Almost fell for it - 'Mashreq Security' call about suspicious activity, then asked for OTP. SCAM!",
    "Please share: Mashreq Bank will NEVER call asking for your OTP or PIN. These are scam calls!",
]


def generate_scenario_1_signals():
    """Generate 70 signals for Digital Dirham Bridge Failure - 50+ in 10 min window"""
    signals = []
    
    # First burst: 55 signals in 10 minutes (viral spike)
    burst_start = BASE_TIME
    for i in range(55):
        timestamp = burst_start + timedelta(seconds=random.randint(0, 600))
        template = random.choice(DIGITAL_DIRHAM_TEMPLATES)
        # Add some variation
        text = template.replace('[USER_ID]', f'[USER_ID_{random.randint(100, 999)}]')
        
        signals.append({
            'event_id': f'dd_{i+1:03d}',
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'raw_text': text,
            'source_platform': get_platform(),
            'user_influence_score': get_influence_score(is_high_urgency=True),
            'scenario': 'Digital_Dirham_Bridge_Failure'
        })
    
    # Second wave: 15 signals spread over next hour (continued concern)
    for i in range(55, 70):
        timestamp = burst_start + timedelta(minutes=random.randint(10, 70))
        template = random.choice(DIGITAL_DIRHAM_TEMPLATES)
        text = template
        
        signals.append({
            'event_id': f'dd_{i+1:03d}',
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'raw_text': text,
            'source_platform': get_platform(),
            'user_influence_score': get_influence_score(),
            'scenario': 'Digital_Dirham_Bridge_Failure'
        })
    
    return signals


def generate_scenario_2_signals():
    """Generate 60 signals for Trusted Device Loop - spread over 3 hours with sarcasm"""
    signals = []
    
    # Spread signals over 3 hours (not viral, but persistent)
    start_time = BASE_TIME + timedelta(hours=2)  # Different time window from scenario 1
    
    for i in range(60):
        timestamp = start_time + timedelta(minutes=random.randint(0, 180))
        template = random.choice(TRUSTED_DEVICE_TEMPLATES)
        text = template
        
        signals.append({
            'event_id': f'td_{i+1:03d}',
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'raw_text': text,
            'source_platform': get_platform(),
            'user_influence_score': get_influence_score(),
            'scenario': 'Trusted_Device_Loop'
        })
    
    return signals


def generate_scenario_3_signals():
    """Generate 70 signals for Security Verification Phishing - 40+ in 15 min"""
    signals = []
    
    # First burst: 45 signals in 15 minutes (viral warning wave)
    burst_start = BASE_TIME + timedelta(hours=5)  # Different time window
    for i in range(45):
        timestamp = burst_start + timedelta(seconds=random.randint(0, 900))
        template = random.choice(PHISHING_WAVE_TEMPLATES)
        text = template
        
        signals.append({
            'event_id': f'ph_{i+1:03d}',
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'raw_text': text,
            'source_platform': get_platform(),
            'user_influence_score': get_influence_score(is_high_urgency=True),
            'scenario': 'Security_Verification_Phishing'
        })
    
    # Continued reports: 25 signals over next 2 hours
    for i in range(45, 70):
        timestamp = burst_start + timedelta(minutes=random.randint(15, 135))
        template = random.choice(PHISHING_WAVE_TEMPLATES)
        text = template
        
        signals.append({
            'event_id': f'ph_{i+1:03d}',
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'raw_text': text,
            'source_platform': get_platform(),
            'user_influence_score': get_influence_score(),
            'scenario': 'Security_Verification_Phishing'
        })
    
    return signals


def main():
    """Generate all signals and write to CSV"""
    all_signals = []
    
    # Generate signals for each scenario
    all_signals.extend(generate_scenario_1_signals())
    all_signals.extend(generate_scenario_2_signals())
    all_signals.extend(generate_scenario_3_signals())
    
    # Sort by timestamp
    all_signals.sort(key=lambda x: x['timestamp'])
    
    # Write to CSV
    output_path = Path(__file__).parent.parent / 'data' / 'synthetic_social_signals_scenarios.csv'
    
    fieldnames = ['event_id', 'timestamp', 'raw_text', 'source_platform', 'user_influence_score', 'scenario']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_signals)
    
    print(f"✅ Generated {len(all_signals)} signals")
    print(f"📁 Saved to: {output_path}")
    
    # Summary
    print("\n📊 Scenario Breakdown:")
    for scenario in ['Digital_Dirham_Bridge_Failure', 'Trusted_Device_Loop', 'Security_Verification_Phishing']:
        count = len([s for s in all_signals if s['scenario'] == scenario])
        print(f"   - {scenario}: {count} signals")


if __name__ == '__main__':
    main()
