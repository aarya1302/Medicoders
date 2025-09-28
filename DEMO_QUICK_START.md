# 🚀 QUICK START - Live ED Simulation Demo

## 📋 Pre-Demo Setup (5 minutes)

### 1. Generate QR Codes

```bash
source venv/bin/activate
cd demo
python qr_generator.py
```

This creates demo cards in `demo/qr_codes/`

### 2. Start WebSocket Server

```bash
# Terminal 1
source venv/bin/activate
python3 -c "from backend.websocket_server import run_server; run_server()"
```

### 3. Start Mobile Form Server

```bash
# Terminal 2
cd mobile
python3 -m http.server 8000
```

### 4. Start Live Dashboard

```bash
# Terminal 3
source venv/bin/activate
python3 -m streamlit run live_dashboard.py --server.port 8501
```

## 🎬 DEMO EXECUTION

### Setup (30 seconds)
1. **Main Screen**: Open dashboard at `http://https://medicoded-dashboard.fly.dev/`
2. **QR Cards**: Print and distribute cards from `demo/qr_codes/`
3. **Test**: Scan one QR code with your phone to verify

### Presentation Flow (5 minutes)

#### 1. **The Calm** (30s)

- Show empty ED dashboard
- "Right now, someone in Perth is having a heart attack..."

#### 2. **The Crisis** (90s)

- "Everyone scan your QR codes - you've all had emergencies!"
- Watch patients flood ED in real-time
- Capacity climbs: 60% → 80% → 95%
- "This is where people die from overcrowding"

#### 3. **AI Salvation** (90s)

- AI intervention automatically triggers at 90%+ capacity
- Watch wait times drop, efficiency improve
- Individual judge phones get updates: "Fast-tracked to bed 15!"

#### 4. **Victory Lap** (60s)

- Show final metrics: $2.4M savings, 1,500% ROI
- "500,000 West Australians - old system or this one?"

## 🔥 WOW FACTOR MOMENTS

- **60+ judges** become patients simultaneously
- **Live capacity crisis** building on screen
- **Individual phone updates** - judges see their own status
- **AI intervention** with dramatic recovery
- **Real ROI calculations** - $2.4M annual savings

## 🆘 TROUBLESHOOTING

**Dashboard not loading?**
- Check `https://medicoded-dashboard.fly.dev/`
- Restart: `streamlit run live_dashboard.py`

**Mobile forms not working?**  
- Check `https://medicoded-form.fly.dev/`
- Restart: `cd mobile && python -m http.server 8000`

**No real-time updates?**

- Check WebSocket server is running
- Test with: `python test_simulation.py`

**QR codes not working?**

- Verify mobile server is running
- Check URL in QR code points to `https://medicoded-form.fly.dev/`

## 💡 SUCCESS TIPS

1. **Practice the timing** - 5 minutes total
2. **Test QR codes** beforehand with your phone
3. **Have backup plan** - manual patient entry if needed
4. **Engage judges** - "You're patient #23, wait time 4.5 hours!"
5. **Build tension** - "We're at critical capacity!"
6. **Dramatic reveal** - "Watch AI save the day!"

## 🏆 WINNING ELEMENTS

✅ **Real-time interactivity** - Judges ARE the patients  
✅ **Spectacular visuals** - Live ED crisis unfolds  
✅ **Emotional journey** - Crisis → Tension → Relief → Victory  
✅ **Business impact** - $2.4M savings, 1,500% ROI  
✅ **Technical excellence** - WebSocket, ML, real-time predictions  
✅ **Clinical relevance** - Realistic ED scenarios and workflows

---

**🎯 YOU'VE GOT THIS!**

This isn't just a demo - it's an **experience** that judges will never forget. They'll feel the ED crisis personally and watch your AI save the day in real-time.

**Good luck at the WA Health Hackathon! 🏥🚀**
