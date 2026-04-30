"""Check IMEI overlap between Blackbelt and Company files"""
import pandas as pd
from mismatch_detector import clean_id

BB_PATH = r"C:\Users\dharm\Downloads\ExcelReports-analyst-14-04-2026-12-12-18.xlsx"
CO_PATH = r"C:\Users\dharm\Downloads\Stack Bulk Upload - 2026-04-14T153918.672.xlsx"

print("Loading Blackbelt file...")
bb = pd.read_excel(BB_PATH, sheet_name="Sheet1")
bb_imeis = set(bb["IMEI/MEID"].map(clean_id).dropna())
print(f"Blackbelt IMEIs: {len(bb_imeis)}")

print("\nLoading Company file...")
co = pd.read_excel(CO_PATH, sheet_name="BulkSell")
co_imeis = set(co["IMEI Number"].map(clean_id).dropna())
print(f"Company IMEIs: {len(co_imeis)}")

overlap = bb_imeis & co_imeis
print(f"\nOverlap: {len(overlap)} IMEIs")
print(f"Percentage of BB IMEIs in Company: {len(overlap)/len(bb_imeis)*100:.1f}%")
print(f"Percentage of Company IMEIs in BB: {len(overlap)/len(co_imeis)*100:.1f}%")

if overlap:
    print(f"\nSample overlapping IMEIs (first 5):")
    for imei in list(overlap)[:5]:
        print(f"  {imei}")
