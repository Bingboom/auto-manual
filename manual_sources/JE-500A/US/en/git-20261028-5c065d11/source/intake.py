"""Write the JE-500A US English semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-500A/US/en/git-20261028-5c065d11/source/intake.py``.
It writes ``source/en/content.json`` and the two declared plain-table rows of
``source_manifest.json:shared_component_exceptions``. ``original.pdf`` is outlined
(no text layer), so every English line below is transcribed from 300 dpi renders
of the named physical page and kept as printed. Every printed block maps to a
shared component or plain shared flow (``source_manifest.json:component_map``);
no package class or inline style. The cover (p1) and contents (p3) are not Web
content.
"""
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import OL, P, UL, Book, blocks, fcc_flow, inbox_carrier, pair, spec_carrier  # noqa: E402
from kit import inline, node, root  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
)
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import (  # noqa: E402
    warranty_lead_component_spec, warranty_section_component_spec, warranty_years_component_spec,
)
from tools.web.frozen_ai_flow import table  # noqa: E402
from tools.web.prepared_style_audit import table_text_sha256  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
DC = "⎓"  # the print's DC symbol


def cell(value: str, *, header: bool = False, **fields) -> dict:
    return node("table_cell", inline(value), header=header, **fields)


def make() -> list[str]:
    b = Book(SOURCE, "JE-500A", "US", "en", "Jackery Explorer 500 · JE-500A")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731
    exceptions = []

    def plain_table(rows, reason):
        flow = table(rows)
        b.add(flow)
        exceptions.append({"kind": "table", "language": "en", "page_id": b.current["id"],
                           "text_sha256": table_text_sha256(root(flow)), "reason": reason})

    # ---- p2 IMPORTANT (the "US" badge marks the language edition) ----------------
    b.chapter("introduction", "IMPORTANT", [2])
    b.add(P("Congratulations on your new Jackery Explorer 500. Please read this manual carefully before "
            "using the product, particularly the relevant precautions to ensure proper use. Keep this "
            "manual in an accessible place for frequent reference."),
          P("In compliance with laws and regulations, the right of final interpretation of this document "
            "and all related documents of this product resides with the Company."),
          P("Please kindly notice that no further notifications will be given in case of any update, revision "
            "or termination."))

    # ---- p4-5 IMPORTANT SAFETY INFORMATION -------------------------------------------
    b.chapter("safety", "IMPORTANT SAFETY INFORMATION", [4, 5])
    b.callout("WARNING", "**INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS**",
              variant="warning")
    b.callout("WARNING", "**Always follow these basic precautions when using this product.**", variant="warning")
    b.add(UL(
        "Read all the instructions before using the product.",
        "Do not allow children to play on the product. Close supervision of children is necessary when the "
        "product is used near children.",
        "Avoid placing hands or fingers inside the product.",
        "Stop using the product immediately if it has been physically damaged or modified. Improper use of the "
        "product may cause unpredictable behavior, leading to fire, explosion, or injury.",
        "If any of the following are observed, including but not limited to overheats, emits unusual odors or "
        "smoking, leaks, or burns, stop using the product immediately and contact the dealer or our Customer Support.",
        "Never attempt to open, repair, or modify the product. Any tampering, reassembly, or modification of the "
        "product can result in electric shock, fire, or battery damage.",
        "Be aware that liquid ejected from the product may cause irritation or burns. Inappropriate or abusive use "
        "may lead to battery leakage. Avoid direct contact with leaking liquid. If the liquid contacts your eyes, "
        "seek medical help immediately. If it contacts other body parts, flush with running water and consult a "
        "medical professional without delay.",
        "Do not expose the product to fire or excessive temperatures. Doing so may result in an explosion if the "
        "temperature exceeds 130°C (265°F).",
        "Any use of unrecommended or non-supplied materials or parts with the product may result in a risk of fire, "
        "electric shock, or personal injury.",
        "Do not leave the battery charging unattended for long periods. Always monitor the charging process to "
        "ensure safe operation.",
        "To reduce the risk of electric shock, unplug the product from any power source before attempting any "
        "technical service or troubleshooting.",
    ))
    b.h("OPERATING INSTRUCTIONS")
    b.h("SAVE THESE INSTRUCTIONS", level=4)
    b.add(UL(
        "Make sure to review your local battery recycling guidelines and find a certified recycling center or "
        "collection point near you for defective battery disposal. Never dispose of batteries in regular household "
        "waste, as they may leak hazardous chemicals or cause fires.",
        "Stop using the product immediately if it shows signs of damage. Discontinue use and contact customer "
        "support for assistance.",
        ("Do not charge the battery in extremely hot or cold environments and strictly adhere to the product's "
         "specified operating temperature ranges :",
         UL("Charging temperature: –4°F to 113°F / -20°C to 45°C;",
            "Discharging temperature: –4°F to 113°F / -20°C to 45°C.")),
        ("To ensure proper air circulation, keep the product vents uncovered. The area where the product is used "
         "must have adequate airflow in a cool, dry environment to prevent overheating.",
         UL("Charging in damp or poorly ventilated spaces may cause safety hazards.",
            "Water can cause short circuits or damage to the charger, leading to safety risks.")),
        "Unplug the power cord from a power outlet during a storm.",
        "Immediately turn off the product by pressing the power button if it has fallen, been dropped, or exposed "
        "to vibrations.",
        "Ensure the device(s) are powered off before connecting it to the product.",
        "Do not charge the product using a damaged or broken charging cord or plug.",
        "Do not use the product to charge any device with a damaged or broken cable or plug.",
        "Always unplug the charging cord by pulling the plug, not the cord, to reduce the risk of damage.",
        "Ensure the product is properly secured when transporting it in a moving vehicle.",
        "DO NOT place the unit upside down or on its side during use or storage.",
        "DO NOT place the product on the floor or at a height less than 18 inches (457 mm) above the floor "
        "during operation in a workshop or repair facility.",
        "DO NOT use the product's accessories with other devices or equipment.",
        "Solar charge time depends on weather conditions, place your solar panel where it will get as much "
        "direct sunlight as possible.",
    ))
    b.callout("DANGER", "**This device is intended for indoor use only (Please place this device in a similar "      # p5
              "indoor environment when using it outdoors， e.g. Home RVs, tents, cabins, etc.).\n"
              "※ This device is not waterproof or dustproof. Keep away from rain and humid environments during use.**",
              variant="danger")
    b.h("USER MAINTENANCE INSTRUCTIONS")
    b.add(P("During the lifecycle of energy storage products, a certain degree of capacity and energy degradation "
            "is expected. As the number of charge and discharge cycles increases and storage time extends, this "
            "degradation will gradually intensify, which is a normal phenomenon consistent with the natural aging "
            "of battery cells."))

    # ---- p5 MEANING OF SYMBOLS, FCC --------------------------------------------------
    b.chapter("symbols", "MEANING OF SYMBOLS", [5])
    headers = [pair("Symbol", "content"), pair("Meaning", "content")]
    rows = [{"label": label, "show_icon": icon, **pair(meaning, "meaning")} for label, icon, meaning in [
        ("WARNING", True, "Hazardous practices that may result in severe injury, death, and/or property damage."),
        ("CAUTION", True, "Hazardous practices that may result in personal injury and/or property damage."),
        ("NOTE", False, "Hazardous practices that may result in equipment damage, data loss, performance "
                        "deterioration, or unanticipated results."),
        ("TIP", False, "Supplements the important information or operation tips in the text."),
    ]]
    b.comp(symbol_signal_component_spec, accessibility_label="Signal words", headers=headers, rows=rows)
    symbols = load("symbols.json")
    panels = [[], []]
    for index, row in enumerate(symbols):
        meaning = pair(row["meaning"], "meaning")
        panels[0 if row["glyph_search_box"][0] < 100 else 1].append(
            {"asset_index": index, "icon_alt": meaning["meaning_text"], **meaning})
    b.comp(symbol_icon_component_spec, accessibility_label="MEANING OF SYMBOLS",
           headers=[pair(v, "content") for v in ("Symbol", "Meaning", "Symbol", "Meaning")],
           panels=panels, icon_refs=[r["local_path"] for r in symbols])
    # The print's FCC block has no opening part 15 conditions paragraph; it starts with NOTE:.
    left = [
        "NOTE: This equipment has been tested and found to comply with the limits for a Class B digital device, "
        "pursuant to part 15 of the FCC Rules. These limits are designed to provide reasonable protection against "
        "harmful interference in a residential installation. This equipment generates, uses and can radiate radio "
        "frequency energy and, if not installed and used in accordance with the instructions, may cause harmful "
        "interference to radio communications. However, there is no guarantee that interference will not occur in a "
        "particular installation. If this equipment does cause harmful interference to radio or television "
        "reception, which can be determined by turning the equipment off and on, the user is encouraged to try to "
        "correct the interference by one or more of the following measures:",
    ]
    measures = ["Reorient or relocate the receiving antenna.",
                "Increase the separation between the equipment and receiver.",
                "Connect the equipment into an outlet on a circuit different from that to which the receiver is "
                "connected.",
                "Consult the dealer or an experienced radio/TV technician for help."]
    modification = ("MODIFICATION: Any changes or modifications not expressly approved by the grantee of this "
                    "device could void the user’s authority to operate the device.")
    paragraph = lambda value: ({"kind": "paragraph", "label": value.split(":")[0] + ":",  # noqa: E731
                                "text": value.split(":", 1)[1].strip()} if value.startswith(("NOTE:", "MODIFICATION:"))
                               else {"kind": "paragraph", "label": "", "text": value})
    b.serial += 1
    fcc = fcc_component_spec(
        accessibility_label="FCC", opening_copy=[], left_blocks=[paragraph(v) for v in left],
        right_blocks=[{"kind": "list", "items": measures}, paragraph(modification)],
        source_ref=f"transcribed-pdf/symbols/{b.serial}", language="en", mark_asset_ref="assets/fcc_mark.svg")
    b.add(fcc_flow(fcc, "", [*left, " ".join("-- " + m for m in measures), modification]))

    # ---- p6-7 WHAT'S IN THE BOX, PRODUCT OVERVIEW ----------------------------------------
    b.chapter("in_the_box", "WHAT'S IN THE BOX", [6])
    slots = ("inbox-unit", "inbox-ac-cable", "inbox-user-manual")
    cards = [{"image_ref": b.figures[slot]["local_path"], "label": b.figures[slot]["caption"],
              "alt": b.figures[slot]["caption"]} for slot in slots]
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="WHAT'S IN THE BOX", cards=cards,
           tip_label="TIP", tip_body="The car charging cable is not included but is available for purchase separately "
                                     "on our website. For assistance, please contact Jackery customer service.",
           variant="responsive-card-grid")
    b.chapter("product_overview", "PRODUCT OVERVIEW", [6, 7])
    b.h("FRONT VIEW")
    b.figure("overview-front")
    b.h("RIGHT SIDE VIEW")                                                            # p7
    b.figure("overview-right")

    # ---- p7-8 LCD DISPLAY -----------------------------------------------------------------
    b.chapter("lcd_display", "LCD DISPLAY", [7, 8])
    b.figure("lcd-display")
    glyphs = load("glyphs.json")
    names = [
        ("1", "UPS", "**On:** The product is in bypass mode, and the switchover time from grid power to the internal "
         "battery is 10 ms.\n**Off:** The product is not in bypass mode."),
        ("2", "AC Power Indicator", "The AC output (pure sine wave) is on."),
        ("3", "Input Power", "Displays the input power in watts."),                                       # p8
        ("4", "Output Power", "Displays the output power in watts."),
        ("5", "AC Wall Charging Indicator", "The product is charged via the AC Input using grid power."),
        ("6", "Car Charging Indicator", "The product is charged via the DC Input (8020) using DC 12V (car charging)."),
        ("7", "Solar Charging Indicator", "The product is charged via the DC Input (8020) using solar panel(s)."),
        ("8", "Battery Power Indicator", "When the product is being charged, the orange circle around the battery "
         "percentage will light up in sequence.\nWhen charging other devices, the orange circle will stay on."),
        ("9", "Remaining Battery Percentage", "Displays the remaining battery percentage."),
        ("10", "Fault Code", "A product error has occurred. Please refer to the Troubleshooting section for details."),
        ("11", "High Temperature Indicator", "High temperature protection is triggered. The product may stop "
         "functioning until its temperature returns to the normal operating range."),
        ("11", "Low Temperature Indicator", "Low temperature protection is triggered. The product may stop "
         "functioning until its temperature returns to the normal operating range."),
        ("12", "Energy Saving Mode", "**On:** Energy Saving Mode is enabled.\n**Off:** Energy Saving Mode is disabled."),
    ]
    rows = [{**pair(number, "number"), **pair(name, "name"), **pair(description, "description"),
             "icon_alt": name, "asset_index": index}
            for index, (number, name, description) in enumerate(names)]
    b.comp(lcd_icon_component_spec, accessibility_label="LCD DISPLAY", rows=rows,
           icon_refs=[g["local_path"] for g in glyphs if g["slot"].startswith("lcd-")],
           icon_locale_policy="exact")

    # ---- p9-11 OPERATIONS -------------------------------------------------------------------
    b.chapter("operations", "OPERATIONS", [9, 10, 11])
    b.h("POWER ON/OFF")
    b.figure("power-on-off")
    b.add(P("* When Energy Saving Mode is enabled and either the AC or DC power button is turned on, the system "
            "will automatically turn off all outputs and shut down if there is no charging or discharging activity, "
            "or if the power consumption of connected devices remains below the defined thresholds for 6 hours (25W "
            "or less on the AC output, and 2W or less on the USB ports and car cigarette lighter port)."))
    b.h("AC OUTPUT ON/OFF")
    b.figure("ac-output")
    b.h("DC/USB OUTPUT ON/OFF")                                                       # p10
    b.figure("dc-usb-output")
    b.add(P("* The product can charge your car battery using the Jackery 12V automobile battery charging cable, "
            "which is sold separately and available on our website."))
    b.callout("Caution", UL(
        "The cigarette lighter port is only compatible with 12V car batteries and not suitable for 24V systems.",
        "Do not start the car while the product is charging the car battery through the 12V DC output port "
        "(cigarette lighter port), as this may damage the product.",
        "This feature is intended for emergency use only and cannot charge a dead or damaged car battery."),
        variant="caution")
    b.h("ENERGY SAVING MODE")
    b.add(P("To prevent unnecessary battery consumption due to forgetting to turn off the output, please manually "
            "enable Energy Saving Mode. Once enabled, if the connected device's power consumption is below a certain "
            "threshold (AC output ≤ 25W; USB output + cigarette lighter port ≤ 2W), the device will automatically "
            "turn off all outputs after 6 hours."))
    b.figure("energy-saving")
    b.h("LED LIGHT ON/OFF")                                                           # p11
    b.add(P("**The LED light has two modes:** Light mode and SOS mode."))
    b.figure("led-light")
    b.add(P("* The default setting is Light mode.\n* In any mode, press and hold the LED light button to turn off the "
            "light."))
    b.h("LCD SCREEN ON/OFF")
    span = {"row_span": 3}
    plain_table([
        [cell("LCD Screen", **span), cell("Turn on"), cell("Press the Main Power Button or when the product is charging.")],
        [cell("Turn off"), cell("Press the Main Power Button.")],
        [cell("Auto-off"), cell("The LCD turns off automatically and enters sleep mode after 2 minutes of inactivity.")],
        [cell("Always-on Display Mode (under charging or discharging state)", **span), cell("Turn on"),
         cell("Double-click the Main Power Button when the LCD screen is ON.")],
        [cell("Turn off"), cell("Press the Main Power Button.")],
        [cell("Auto-off"), cell("The Always-on Display Mode turns off automatically after 2 hours of inactivity.")],
    ], "HB-TABLE-LCD-MODE requires its button artwork; this print sets the LCD SCREEN ON/OFF table without any "
       "drawing, so the printed three-column state/action/description table is kept as a plain shared table.")

    # ---- p12 UNINTERRUPTIBLE POWER SUPPLY (UPS) -------------------------------------------------
    b.chapter("ups", "UNINTERRUPTIBLE POWER SUPPLY (UPS)", [12])
    b.add(P("An uninterruptible power supply (UPS) is a type of continual power system that provides automated backup "
            "electric power to a load when the mains grid power fails."),
          P("In the event of a sudden loss of grid power, the Explorer 500 will automatically switch to stored power "
            "within 10 ms to keep your appliances running."))
    b.figure("ups")
    # The print's grey "Important Notes:" box carries no signal word: plain bold lead + numbered list.
    b.add(P("**Important Notes:**"), OL(
        "This product does not support 0 ms switching. Do not connect it to equipment that requires an "
        "uninterrupted power supply, such as data servers or workstations.",
        "Before use, please test compatibility with your device multiple times.",
        "It is recommended to connect one device at a time. Do not use multiple devices simultaneously, as this may "
        "trigger overload protection."))

    # ---- p13-14 CHARGING ----------------------------------------------------------------------
    b.chapter("charging", "CHARGING", [13, 14])
    b.add(P("**Green energy first:** We advocate to use the green energy first. This product supports two modes of "
            "charging at the same time: solar charging and AC wall charging.\nWhen AC wall charging and solar "
            "charging are turned on at the same time, the product will give priority to solar charging and both "
            "methods will be used to charge the battery at the maximum permissible power."),
          P("**Fully charge the product before its first use.**"))
    b.callout("Note", OL(
        "The recommended charging temperature for the product ranges from –4°F to 113°F / -20°C to 45°C, and the "
        "discharging temperature ranges from –4°F to 113°F / -20°C to 45°C. Operating the product outside this "
        "temperature range may restrict its charging and discharging capabilities, prevent it from charging or "
        "discharging.",
        "The charging power and battery capacity of the product may vary due to temperature fluctuations."),
        variant="note")
    b.h("CHARGING VIA AC WALL OUTLET")
    b.figure("charging-ac")
    b.add(P("* Make sure the AC charging cable is fully and securely plugged into the AC input port. An incomplete "
            "connection may cause unstable current, overheating, poor contact, or device malfunction."))
    b.h("CHARGING WITH SOLAR PANELS")
    b.add(P("The Jackery Explorer 500 has one DC8020 input port, which supports direct connection of either one 100W "
            "or one 200W solar panel. If you need to connect two 100W solar panels simultaneously to a DC8020 input "
            "port, please use a solar panel connector (sold separately, not included). Please refer to the diagram "
            "below for connection details."))
    b.figure("charging-solar-200")
    b.figure("charging-solar-2x100")                                                  # p14
    b.callout("CAUTION", "It is recommended to use the Jackery solar panel to charge the Jackery Explorer 500. Ensure "
              "that the open-circuit voltage (V_{oc}) of the solar panel falls within the Jackery Explorer 500's DC "
              "input voltage range (16V–60V). Jackery is not responsible for any damage or loss resulting from the use "
              "of third-party solar panels.", variant="caution")
    b.h("CHARGING WITH A CAR CHARGER")
    b.add(P("This product can be charged using a 12V car charger. Ensure that the car charger and the car cigarette "
            "lighter provide a good connection."))
    b.figure("charging-car")
    b.callout("CAUTION", OL(
        "Please start the vehicle before charging your product.",
        "If the vehicle is running on bumpy roads, it is forbidden to use the car charger in case it burns due to a "
        "poor connection. The Company will not be responsible for any loss caused by non-standard operation.",
        "Vehicle charging is only applicable to vehicles with 12V DC, not 24V DC. Please do not charge this product "
        "in 24V vehicle to avoid personal injury and property loss.",
        "It is recommended to use the Jackery Solar Panel to charge the Explorer 500. Jackery is not responsible for "
        "any losses caused by using solar panels from other brands."), variant="caution")

    # ---- p15 STORAGE, TROUBLESHOOTING -------------------------------------------------------------
    b.chapter("storage", "STORAGE", [15])
    b.add(P("Store the product in a dry clean place with proper ventilation. Storage temperature and humidity:"),
          UL("1 month: -4°F to 113°F / -20°C to 45°C (0-60%RH)",
             "3 months: 32°F to 113°F / 0°C to 45°C (0-60%RH)",
             "12 months: 32°F to 77°F / 0°C to 25°C (0-60%RH)"),
          P("If this product is stored for a long period of time (3 months - 6 months) with the power depleted, it may "
            "become unchargeable. To prevent this and maintain battery health, it is recommended to check and recharge "
            "the product every three months and perform a full charge and discharge cycle at least once every 6 to 12 "
            "months."))
    b.chapter("troubleshooting", "TROUBLESHOOTING", [15])
    faults = [
        ("F0", "BMS Data Communication Error", "Data communication failure between the BMS and mainboard"),
        ("F1", "Inverter Data Communication Error", "Data communication failure between the inverter and mainboard"),
        ("F2", "DC Input Data Communication Error", "Data communication failure between the DC charging module and BMS"),
        ("F3", "BMS or Battery Failure", "BMS or battery failuare"),
        ("F4", "Battery Overvoltage", "Battery overvoltage"),
        ("F5", "Battery Undervoltage", "Battery undervoltage"),
        ("F6", "Inverter Failure", "AC output overcurrent / overload / short circuit protection triggered\nGrid input "
         "over-voltage / undervoltage / overfrequency / underfrequency protection triggered\nInverter over-temperature "
         "protection triggered\nInsulation detection failure"),
        ("F7", "DC Charging Module (PV) Failure", "PV input overvoltage;\nDC charging module overtemperature protection "
         "on/triggered;\nOutput overcurrent protection of the DC charging module on/triggered"),
        ("F8", "Battery Charging / Discharging Overcurrent / Short Circuit", "BMS overcurrent / short circuit protection "
         "triggered"),
        ("F9", "DC Output Overcurrent / Short Circuit", "USB short circuit protection triggered"),
    ]
    plain_table([[cell("**Error Code**", header=True), cell("**Name**", header=True),
                  cell("**Description (For Internal Fault Maintenance Only)**", header=True)]]
                + [[cell(f"**{code}**"), cell(f"**{name}**"), cell(text)] for code, name, text in faults],
                "HB-TABLE-TROUBLESHOOTING is two-column (error code + corrective measures); this print's fault table "
                "has three columns (Error Code / Name / Description for internal fault maintenance) and no corrective "
                "measures, so it is kept as a plain shared table.")

    # ---- p16 SPECIFICATIONS ----------------------------------------------------------------------
    b.chapter("specifications", "SPECIFICATIONS", [16])
    for title, rows in [
        ("GENERAL INFO", [("Product Name", "Jackery  Explorer 500"), ("Model No.", "JE-500A"),
                          ("Capacity", "20Ah/25.6Vdc (512Wh)"), ("Cell Chemistry", "LiFePO₄"),
                          ("Weight", "About 12.57 lbs/5.7kg"), ("Dimensions", "12.2×8.1×6.2 in / 31.1×20.5×15.7 cm"),
                          ("Cycle Life", "6000 cycles to 70%+ capacity")]),
        ("INPUT PORTS", [("Charge Mode AC Input", "100-120V~ 60Hz, 15A Max"),
                         ("1 × DC8020 Port", f"11V-16V{DC}8A Max"), ("", f"16V-60V{DC}10.5A, 200W Max")]),
        ("OUTPUT PORTS", [("2 × AC Output", "120V~ 60Hz, 4.2A"),
                          ("Bypass Mode AC Output", "100V-120V~ 60Hz, 500W"),
                          ("AC Total Output", "500W Rated, 1000W Surge Peak"),
                          ("USB-C1 Output", f"100W Max, 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A"),
                          ("USB-C2 Output", f"30W Max, 5V{DC}3A, 9V{DC}3A, 12V{DC}2.5A, 15V{DC}2A, 20V{DC}1.5A"),
                          ("USB-A Output", f"18W Max, 5-6V{DC}3A, 6-9V{DC}2A, 9-12V{DC}1.5A"),
                          ("Cigarette Lighter Port", f"12V{DC}10A Max")]),
        ("ENVIRONMENTAL OPERATING TEMPERATURE", [("Charge Temperature", "–4°F to 113°F / -20°C to 45°C"),
                                                 ("Discharge Temperature", "–4°F to 113°F / -20°C to 45°C")]),
    ]:
        b.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows)
    b.add(P("※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."))

    # ---- p17 WARRANTY ----------------------------------------------------------------------------
    b.chapter("warranty", "WARRANTY", [17])
    b.comp(warranty_lead_component_spec, accessibility_label="WARRANTY",
           lead_html="<strong>We only provide our warranty to customers who purchase from the official Jackery website, "
                     "Jackery-branded third-party platforms, or local authorized dealers.</strong>",
           local_note_html="*Warranty period and details may vary according to local laws, regulations, and authorized "
                           "dealers.")
    sections = [
        ("Limited Warranty", blocks(
            "Jackery Inc. warrants to the original consumer purchaser that the Jackery product will be free from defects "
            "in workmanship and material under normal consumer use during the applicable warranty period identified in "
            "the 'Warranty Period' section below, subject to the exclusions set forth below.",
            "This warranty statement sets forth Jackery's total and exclusive warranty obligation. We will not assume, "
            "nor authorize any person to assume for us, any other liability in connection with the sale of our "
            "products.")),
        ("Warranty Period", None),
        ("Repair or replacement", blocks(
            "Jackery will repair or replace (at Jackery's expense) any Jackery product that fails to operate during the "
            "applicable warranty period due to a defect in workmanship or material. The repaired/replaced product "
            "assumes the remaining warranty of the original date of purchase.")),
        ("Limited to Original Consumer Buyer", blocks(
            "The warranty on Jackery's product is limited to the original consumer purchaser and is not transferable "
            "to any subsequent owner.")),
        # The print sets the exclusions as plain paragraphs (no bullets, lead not bold).
        ("Exclusions", blocks(
            "Jackery's warranty does not apply to:",
            "Misused, abused, modified, damaged by accident, or used for anything other than normal consumer use as "
            "authorized in Jackery's current product literature.",
            "Attempted repair by anyone other than an authorized facility.",
            "Any product purchased through an online auction house.",
            "Jackery's warranty does not apply to the battery cell unless the battery cell is fully charged by you "
            "within seven days after you purchase the product and at least once every 6 months thereafter.")),
        ("Interpretation Rights", blocks(
            "Jackery reserves the right to final interpretation of the above customers' after-sales policy.")),
    ]
    for index, (title, body) in enumerate(sections, start=1):
        b.h(title)
        if body is None:
            b.comp(warranty_years_component_spec, title=title, periods=[
                {"number": "3", "unit": "YEARS", "label": "Standard Warranty",
                 **{k: v for k, v in zip(("body_html", "body_text"), strict=True, *[_body(
                     "The standard warranty period for Jackery Explorer 500 is 36 months. In each case, the warranty "
                     "period is measured starting on the date of purchase by the original consumer purchaser. The sales "
                     "receipt from the first consumer purchase, or other reasonable documentary proof, is required in "
                     "order to establish the start date of the warranty period.")])}},
                {"number": "2", "unit": "YEARS", "label": "Extended Warranty",
                 **{k: v for k, v in zip(("body_html", "body_text"), strict=True, *[_body(
                     "To activate the Warranty Extension, you must register your product online  or contact our "
                     "customer service team at hello@jackery.com to extend the standard warranty runtime.")])}},
            ])
            continue
        b.comp(warranty_section_component_spec, title=title, section_index=index, blocks=body)

    # ---- p18 back cover: contact -------------------------------------------------------------------
    b.chapter("contact", "JACKERY INC.", [18])
    b.add(P("5310 Bunche Dr., Fremont, CA 94538-8301"),
          P("1-888-502-2236 (US)\nhello@jackery.com\nwww.jackery.com"))
    b.figure("contact-qr")

    problems = b.finish()
    manifest_path = SOURCE / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["shared_component_exceptions"] = exceptions
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("chapters", len(b.chapters), "problems", problems)
    return problems


def _body(value: str):
    import html
    return "<p>" + html.escape(value) + "</p>", value


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
