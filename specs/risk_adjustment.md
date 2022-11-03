# Risk Adjustment

## Motivation
- Holding 4 bossbeauties in inventory on 2022-03-24, worth about 8 eth. Considering buying a 5th BB, but at some point must consider max risk tolerance within one collection. Should buy each successive BB for more and more edge_ratio based on inventory. If a BB is sold then inventory decreases, so minimum edge_ratio to trade can decrease.
- Ideally would have some level awareness but not as necessary

## Logic
Concept of "adjusted theoretical value". Instead of calculating edge and edge_ratio relative to TV, calculate relative to adjusted TV. Required edge and edge_mult concepts remain the same.