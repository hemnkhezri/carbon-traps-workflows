# ENTSO-E study: deviations and corrections (EXT4_PREREG.md)

1. **Description, not design (10 Nov 2026, after the results).** Section 3 of the plan says that M3 had the
   lowest mean absolute error on both zones. On ES it tied with M2 (20.1 g/kWh at one decimal); on DE-LU it
   was lowest (32.9 against 36.1 and 37.7). The model used is unchanged.
2. **Code fix before sealing (10 Nov 2026).** While building the vintages on development data, the capture
   time of the day after a daylight-saving change was off by a day because a fixed 24-h offset was used; it
   was replaced by a calendar-day offset in `cwf/entsoe.py` before the plan was sealed. The model-selection
   numbers in Section 3 come from an earlier exploratory script with the fixed offset; they affect only 2 of
   366 development days per zone.
