# Dashboard wireframe

The pen-and-paper sketch the implementation is based on. Redraw this by hand
and drop a photo here (`sketch.jpg`) before submitting the assignment.

```
┌──────────────────────────────────────────────────────────────────────┐
│ (S) Stride · Six years on foot                       [ Dec 2019–Jun 26 ]│
├──────────┬───────────────────────────────────────────────────────────┤
│ FILTERS  │  [ Overview ]  Explorer   Physiology   About                │
│          │ ───────────────────────────────────────────────────────── │
│ Date     │  ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐   KPI cards           │
│ range    │  │711 ││km  ││time││pace││elev││VO2 │                       │
│          │  └────┘└────┘└────┘└────┘└────┘└────┘                       │
│ Sport    │  ┌──────────────────────────────────────────────────────┐ │
│ [x] run  │  │ Training volume (bars = km, line = count)             │ │
│ [x] bike │  └──────────────────────────────────────────────────────┘ │
│ [x] walk │  ┌───────────────────────────────┐┌─────────────────────┐ │
│          │  │ Pace progression (scatter+avg)││ Activity mix (donut)│ │
│ Distance │  └───────────────────────────────┘└─────────────────────┘ │
│ [==o===] │  ┌───────────────────────────────┐┌─────────────────────┐ │
│          │  │ Monthly distance calendar      ││ HR-zone distribution│ │
│ Weekly o │  └───────────────────────────────┘└─────────────────────┘ │
│ [Reset]  │                                                            │
└──────────┴───────────────────────────────────────────────────────────┘

Explorer tab:
  [ Effort-vs-pace scatter ]   [ Map of run starts ]
  [ Activities datatable    ]   [ Run detail panel ]   ← select row/point → detail+map update
```
