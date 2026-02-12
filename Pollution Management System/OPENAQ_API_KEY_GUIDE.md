# 🔧 OpenAQ Integration Update - API Key Required

## ⚠️ Issue: OpenAQ Shows "Unavailable"

### Root Cause
**OpenAQ V2 API has been retired** and the new **V3 API requires a free API key**.

Error from OpenAQ V2:
```
"Gone. Version 1 and Version 2 API endpoints are retired and no longer available. 
Please migrate to Version 3 endpoints."
```

V3 API Response without key:
```
"Unauthorized. A valid API key must be provided in the X-API-Key header."
```

---

## ✅ Solution: Get Free OpenAQ API Key

### Step 1: Register for Free API Key

1. **Visit**: https://explore.openaq.org/register
2. **Sign up** with your email
3. **Verify** your email address
4. **Generate** API key from your dashboard
5. **Copy** the key

### Step 2: Add API Key to Backend

Open [backend/routes/aqi.py](backend/routes/aqi.py) and find this line (around line 197):

```python
OPENAQ_API_KEY = None  # Add your OpenAQ API key here
```

Replace with your key:

```python
OPENAQ_API_KEY = "your_api_key_here"  # Get free key at https://explore.openaq.org/register
```

### Step 3: Restart Server

```bash
# Stop server (Ctrl+C)
# Restart
python app.py
```

### Step 4: Refresh Browser

Open your dashboard and you'll see **both WAQI and OpenAQ** showing real-time data side-by-side!

---

## 📊 Current Status

### ✅ Working: WAQI
- **Status**: Active and working
- **API Key**: Already configured (`752f88867cdc07ae8736875beb47539dbdc3c544`)
- **Coverage**: 12,000+ monitoring stations worldwide
- **Cost**: Free forever
- **Rate Limit**: 1000 requests/minute
- **Data Quality**: Excellent

### ⚠️ Needs Setup: OpenAQ V3
- **Status**: Requires API key
- **Coverage**: Global monitoring network
- **Cost**: Free tier available
- **Registration**: https://explore.openaq.org/register
- **Rate Limit**: Depends on plan (free tier is generous)
- **Data Quality**: Good

---

## 🔍 What Changed?

### Before (OpenAQ V2 - Retired)
```
GET https://api.openaq.org/v2/latest?coordinates=28.6139,77.2090
→ Returns data without authentication
```

### After (OpenAQ V3 - Current)
```
GET https://api.openaq.org/v3/locations?coordinates=28.6139,77.2090
Headers: X-API-Key: your_key_here
→ Returns data with authentication
```

---

## 💡 Why Both APIs?

Having both WAQI and OpenAQ provides:

### Benefits
1. **Data Validation**: Cross-verify AQI readings
2. **Redundancy**: If one fails, the other works
3. **Coverage**: Different stations, more data points
4. **Accuracy**: Compare readings from multiple sources
5. **Transparency**: Users see data sources clearly

### Example Output
```
┌─────────────────────┬─────────────────────┐
│       WAQI          │      OpenAQ         │
├─────────────────────┼─────────────────────┤
│ AQI: 187           │ AQI: 165            │
│ Category: Moderate  │ Category: Moderate  │
│ PM2.5: 187         │ PM2.5: 156          │
│ PM10: 168          │ PM10: 142           │
│ Station: Dr. Karni  │ Station: Delhi     │
│ Singh Shooting      │ Monitor             │
│ Range, Delhi        │                     │
└─────────────────────┴─────────────────────┘
```

---

## 🆓 OpenAQ Free Tier

### Limits
- **Requests**: 5,000 per day
- **Rate Limit**: 100 requests per minute
- **Data Access**: Full global coverage
- **Cost**: $0 forever

### Paid Tiers
- **Pro**: $99/month - 100,000 requests/day
- **Enterprise**: Custom pricing - Unlimited

For personal projects, **free tier is sufficient**.

---

## 🧪 Test OpenAQ After Setup

### Backend Test
```bash
curl "http://127.0.0.1:5000/aqi/current?lat=28.6139&lng=77.2090"
```

Look for:
```json
{
  "waqi": { "aqi": 187, ... },
  "openaq": { "aqi": 165, ... }
}
```

### Frontend Test
1. Open: http://127.0.0.1:5000/public_aqi.html
2. Check source comparison cards
3. Both WAQI and OpenAQ should show data

---

## 🚨 Current Behavior (Without Key)

### What You See
- ✅ **WAQI Card**: Shows AQI with station name
- ⚠️ **OpenAQ Card**: Shows "Unavailable" with link to register

### Backend Log
```
OpenAQ V3: Skipped - No API key configured. Get free key at https://explore.openaq.org/register
```

### Frontend Message
```
⚠️ Requires API key (Get free key)
```

---

## 📝 Code Changes Made

### Backend ([aqi.py](backend/routes/aqi.py))
1. ✅ Updated to OpenAQ V3 API
2. ✅ Added API key support
3. ✅ Added skip logic when key is missing
4. ✅ Returns both WAQI and OpenAQ in response
5. ✅ Improved error handling

### Frontend ([public-aqi-dashboard.js](frontend/js/public-aqi-dashboard.js))
1. ✅ Added side-by-side comparison cards
2. ✅ Shows helpful message for missing API key
3. ✅ Links to registration page
4. ✅ Displays station names for both sources

---

## 🎯 Quick Start Guide

### If You Want OpenAQ Data:

**5-Minute Setup**:
1. Register → https://explore.openaq.org/register
2. Get API key → Dashboard → Create New Key
3. Add to code → `OPENAQ_API_KEY = "your_key"`
4. Restart server → `python app.py`
5. Refresh browser → Both sources working! ✅

### If You're Happy with Just WAQI:

**Nothing to do!** WAQI is already working perfectly and covers most locations worldwide.

---

## 📚 API Documentation

### OpenAQ V3 Docs
- Main Docs: https://docs.openaq.org/
- API Reference: https://docs.openaq.org/reference
- Registration: https://explore.openaq.org/register

### WAQI Docs
- Main Docs: https://aqicn.org/api/
- Already configured in your project
- No changes needed

---

## ❓ FAQs

### Q: Is OpenAQ really free?
**A**: Yes! 5,000 requests/day free forever.

### Q: Do I need both WAQI and OpenAQ?
**A**: No. WAQI alone is sufficient. OpenAQ adds validation and redundancy.

### Q: Which is better - WAQI or OpenAQ?
**A**: WAQI has better coverage. OpenAQ has more transparency. Use both!

### Q: What if I don't want to register?
**A**: No problem! Just ignore OpenAQ. WAQI works great alone.

### Q: Can I use other sources?
**A**: Yes! See [REAL_AQI_INTEGRATION_GUIDE.md](REAL_AQI_INTEGRATION_GUIDE.md) for alternatives like CPCB, IUDX, etc.

### Q: Why does OpenAQ show "Unavailable" even with a key?
**A**: Some regions have limited OpenAQ coverage. Try different locations or stick with WAQI.

---

## 🎉 Success!

Once configured, your dashboard will show:

```
┌─────────────────────────────────────────────┐
│   Your Current Location AQI: 187 (Moderate)│
├─────────────────────────────────────────────┤
│   ┌──────────────┬──────────────┐          │
│   │   WAQI       │   OpenAQ     │          │
│   │   187        │   165        │          │
│   │   Moderate   │   Moderate   │          │
│   │   Dr. Karni  │   Delhi      │          │
│   │   Singh...   │   Monitor    │          │
│   └──────────────┴──────────────┘          │
└─────────────────────────────────────────────┘
```

**Both sources working side-by-side!** 🌍✨

---

*Last Updated: February 10, 2026*
*Status: OpenAQ V3 migration complete, API key required*
