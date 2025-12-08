# Weather Graphs - Status & Behavior

**Date**: 2025-12-04  
**Status**: ✅ Single-Line Graph (Main Station)  
**Page**: http://localhost:7777/weather

---

## Current Behavior

### Graph Shows: **SINGLE LINE** (Main Station Only)

**Switchable BY:**
- ✅ **Metric Type** (via tabs): Temperature, Humidity, CO2, Pressure
- ✅ **Time Range** (via buttons): 24h, 7d, 30d

**NOT Switchable:**
- ❌ Multiple modules NOT shown together yet
- Graph shows only Main Station (70:ee:50:3a:0e:dc) historical data
- Bathroom module NOT included in graph (yet)

---

## Your Data Sources

### **Main Station** (Graphed ✅)
- Location: Stroheckgasse
- Data: Temperature, Humidity, CO2, Noise, Pressure
- Historical data stored and displayed in graph
- Updates every 30 seconds

### **Bathroom Module** (Cards Only ⚠️)
- Current data shown in station card ✅
- Temperature: 26.6°C
- Humidity: 40%
- CO2: 843 ppm
- Battery: 60%
- **NOT yet in historical graphs** ⚠️

---

## What You See Now

### **Weather Station Cards** (Both Modules) ✅
```
Main Station (Indoor)
├─ Temperature: 26.8°C
├─ Humidity: 34%
├─ CO2: 905 ppm
├─ Noise: 38 dB
└─ Pressure: 1007.3 hPa

Bathroom Module (Indoor Extra) ✅
├─ Temperature: 26.6°C
├─ Humidity: 40%
├─ CO2: 843 ppm
└─ Battery: 60%
```

### **Historical Graphs** (Main Station Only)
```
📊 Graph shows: Main Station data
   - Temperature: Single red line
   - Humidity: Single blue line
   - CO2: Single green line
   - Pressure: Single purple line
   
⚠️  Bathroom module: Not in graph yet
   (Coming soon: dual-line comparison!)
```

---

## Added Visual Indicator

Added info box above graphs:
```
📍 Data Source: Main Station (70:ee:50:3a:0e:dc at Stroheckgasse)

Note: Bathroom module shows current readings in cards above.
Historical graphing for multiple modules coming soon!
```

This makes it clear the graph only shows main station data currently.

---

## Enhancement Opportunity

### **Future: Dual-Line Comparison**

Would allow you to see both modules on same graph:

**Temperature Graph Example:**
```
📊 Temperature (Last 24h)
   Red line:    Main Station (26.8°C)
   Orange line: Bathroom (26.6°C)
```

**Benefits:**
- Compare main station vs bathroom temperature
- See humidity differences between rooms
- Compare CO2 levels (bathroom 843 vs main 905)
- Track which room gets warmer/cooler

**Implementation needed:**
1. Store bathroom module data to time-series database
2. Create API endpoint for per-module historical data
3. Update JavaScript to load both datasets
4. Add legend showing both lines

**Estimated effort:** 2-3 hours

---

## Current Graph Features ✅

### **Working Now:**
- ✅ 4 metric types (temp, humidity, CO2, pressure)
- ✅ 3 time ranges (24h, 7d, 30d)
- ✅ Real-time main station data
- ✅ CO2 threshold lines (800 ppm warning, 1000 ppm danger)
- ✅ Interactive tooltips
- ✅ Smooth animations
- ✅ Auto-refresh every 30 seconds
- ✅ Responsive design

### **Module Coverage:**
- ✅ Main Station: Full historical graphing
- ⚠️ Bathroom: Current readings only (cards)
- ⚠️ Bathroom: Historical graphing pending

---

## Answer to Your Question

**Q: Is the graph switchable or does it show both data lines?**

**A:** Currently it shows a **SINGLE line** (Main Station only).

It's switchable between:
- Metric types (4 tabs)
- Time ranges (3 buttons)

But it does **NOT show both modules** (main + bathroom) as separate lines on the same graph yet.

**What you have now:**
- Main Station: ✅ Live graph
- Bathroom: ✅ Current readings in cards
- Bathroom: ❌ Not in historical graph

**To get dual-line comparison:**
- Would need backend enhancement to store per-module historical data
- JavaScript already prepared for it (`values_bathroom` arrays added)
- Visual styling ready (different colors for each module)

---

## Workaround

For now, you can:
1. **Compare current readings** in the station cards (refreshes every 60 sec)
2. **View main station trends** in the historical graph
3. **Monitor bathroom readings** for differences

Example comparison from current data:
- Main: 26.8°C, 34% humidity
- Bathroom: 26.6°C, 40% humidity
- **Difference**: Bathroom is 0.2°C cooler but 6% more humid (expected!)

---

**Summary**: Graph currently shows SINGLE line (main station). Bathroom module shows in cards but not graphs yet. Enhancement possible if you want dual-line comparison! 📊

