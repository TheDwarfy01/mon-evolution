#!/usr/bin/env python3
"""v1.6.78 — align monthly and weekly loss metrics and place progression last."""
from pathlib import Path
page=Path("android/source-1.6.78/app/src/main/assets/index.html")
s=page.read_text(encoding="utf-8")
old=""" tile('Perte par mois',monthText);
 tile('Progression',fmt(progress)+' %');
 tile('IMC actuel',fmt(currentBmi)+' · '+category);
 tile('Perte / semaine (28 j)',rate===null?'—':fmt(rate*7)+' kg');"""
new=""" tile('Perte / mois',monthText);
 tile('Perte / semaine',rate===null?'—':(rate>0?'−':rate<0?'+':'')+fmt(Math.abs(rate*7))+' kg');
 tile('IMC actuel',fmt(currentBmi)+' · '+category);
 tile('Progression',fmt(progress)+' %');"""
assert s.count(old)==1, "Expected consecutive summary tiles not found"
s=s.replace(old,new,1)
assert s.count("tile('Perte / mois',monthText)") ==1
assert s.count("tile('Perte / semaine'")==1
assert s.count("tile('Progression',fmt(progress)") ==1
page.write_text(s,encoding="utf-8")
print("OK 1.6.78: Perte / mois and Perte / semaine together, signed negative for loss, progression below")
