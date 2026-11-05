"""Write the JE-300E-SG US English semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-300E-SG/US/en/git-20261027-e47cb322/source/intake.py``.
It writes ``source/en/content.json``. ``original.pdf`` is outlined (no text
layer), so every English line below is transcribed from 300 dpi renders of the
named physical page and kept as printed. Every printed block maps to a shared
component or plain shared flow (``audit/component-map.json``); no package class,
inline style or plain table. The cover (p1) and contents (p3) are not Web content.
"""
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import P, UL, Book, blocks, cell_pair, fcc_flow, inbox_carrier, pair, spec_carrier  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import (  # noqa: E402
    warranty_lead_component_spec, warranty_section_component_spec, warranty_years_component_spec,
)

SOURCE = Path(__file__).resolve().parents[1]
DC = "⎓"  # the print's DC symbol


def make() -> list[str]:
    b = Book(SOURCE, "JE-300E-SG", "US", "en", "Jackery Explorer 300 · JE-300E-SG")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731

    # ---- p2 IMPORTANT (the "US" badge marks the language edition) ----------------
    b.chapter("introduction", "IMPORTANT", [2])
    b.add(P("Congratulations on your new Jackery Explorer 300. Please read this manual carefully before "
            "using the product, particularly the relevant precautions to ensure proper use. Keep this "
            "manual in an accessible place for frequent reference."),
          P("In compliance with laws and regulations, the right of final interpretation of this document "
            "and all related documents of this product resides with the Company."),
          P("Please kindly notice that no further notifications will be given in case of any update, revision "
            "or termination."))

    # ---- p4 IMPORTANT SAFETY INFORMATION ---------------------------------------------
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
        "Stop using the product immediately if it shows signs of damage. Discontinue use and contact customer "
        "support for assistance.",
        ("Do not charge the battery in extremely hot or cold environments and strictly adhere to the product's "
         "specified operating temperature ranges:",
         UL("Charging temperature: 32°F to 113°F (0°C to 45°C )",
            "Discharging temperature: 5°F to 113°F (-15°C to 45°C )")),
        ("To ensure proper air circulation, keep the product vents uncovered. The area where the product is used "
         "must have adequate airflow in a cool, dry environment to prevent overheating.",
         UL("Charging in damp or poorly ventilated spaces may cause safety hazards.",
            "Water can cause short circuits or damage to the charger, leading to safety risks.")),
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
    b.callout("DANGER", "**This device is intended for indoor use only (Please place this device in a similar "
              "indoor environment when using it outdoors， e.g. Home RVs, tents, cabins, etc.).\n"
              "※ This device is not waterproof or dustproof. Keep away from rain and humid environments during use.**",
              variant="danger")
    b.h("USER MAINTENANCE INSTRUCTIONS")                                              # p5
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
    opening = ("This device complies with part 15 of the FCC Rules. Operation is subject to the following two "
               "conditions: (1) This device may not cause harmful interference, and (2) this device must accept "
               "any interference received, including interference that may cause undesired operation.")
    left = [
        "NOTE: This equipment has been tested and found to comply with the limits for a Class B digital device, "
        "pursuant to part 15 of the FCC Rules.",
        "These limits are designed to provide reasonable protection against harmful interference in a residential "
        "installation. This equipment generates, uses and can radiate radio frequency energy and, if not installed "
        "and used in accordance with the instructions, may cause harmful interference to communications. However, "
        "there is no guarantee that radio interference will not occur in a particular installation.",
        "If this equipment does cause harmful interference to radio or television reception, which can be "
        "determined by turning the equipment off and on, the user is encouraged to try to correct the interference "
        "by one or more of the following measures:",
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
        accessibility_label="FCC", opening_copy=[opening], left_blocks=[paragraph(v) for v in left],
        right_blocks=[{"kind": "list", "items": measures}, paragraph(modification)],
        source_ref=f"transcribed-pdf/symbols/{b.serial}", language="en", mark_asset_ref="assets/fcc_mark.svg")
    b.add(fcc_flow(fcc, opening, [*left, " ".join("• " + m for m in measures), modification]))

    # ---- p6 WHAT'S IN THE BOX, PRODUCT OVERVIEW ----------------------------------------
    b.chapter("in_the_box", "WHAT'S IN THE BOX", [6])
    cards = [{"image_ref": b.figures[slot]["local_path"], "label": b.figures[slot]["caption"],
              "alt": b.figures[slot]["caption"]}
             for slot in ("inbox-unit", "inbox-ac-adapter", "inbox-car-cable", "inbox-documents")]
    b.used_figures += ["inbox-unit", "inbox-ac-adapter", "inbox-car-cable", "inbox-documents"]
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="WHAT'S IN THE BOX", cards=cards,
           tip_label="", tip_body="", require_tip=False, variant="responsive-card-grid")
    b.chapter("product_overview", "PRODUCT OVERVIEW", [6])
    b.h("FRONT VIEW")
    b.figure("overview-front")

    # ---- p7-8 LCD DISPLAY -----------------------------------------------------------------
    b.chapter("lcd_display", "LCD DISPLAY", [7, 8])
    b.figure("lcd-display")
    glyphs = load("glyphs.json")
    names = [
        ("1", "AC Power Indicator", "The AC output (pure sine wave) is on."),
        ("2", "Output Voltage and Frequency", "Displays the output voltage and frequency."),
        ("3", "Input Power", "Displays the input power in watts."),
        ("4", "Output Power", "Displays the output power in watts."),
        ("5", "Car Charging Indicator", "The product is charged via the DC Input (DC8020) using DC 12V (car charging)."),
        ("6", "Solar Charging Indicator", "The product is charged via the DC Input (DC8020) using solar panel(s)."),
        ("7", "Battery Power Indicator", "When the product is being charged, the orange circle around the battery "
         "percentage will light up in sequence.\nWhen charging other devices, the orange circle will stay on."),
        ("8", "Remaining Battery Percentage", "Displays the remaining battery percentage."),
        ("9", "Fault Code", "A product error has occurred. Please refer to the Troubleshooting section for details."),
        ("10", "High Temperature Indicator", "High temperature protection is triggered. The product may stop "
         "functioning until its temperature returns to the normal operating range."),
        ("10", "Low Temperature Indicator", "Low temperature protection is triggered. The product may stop "
         "functioning until its temperature returns to the normal operating range."),
        ("11", "Energy Saving Mode", "On: Energy Saving Mode is enabled.\nOff: Energy Saving Mode is disabled."),
    ]
    rows = [{**pair(number, "number"), **pair(name, "name"), **pair(description, "description"),
             "icon_alt": name, "asset_index": index}
            for index, (number, name, description) in enumerate(names)]
    b.comp(lcd_icon_component_spec, accessibility_label="LCD DISPLAY", rows=rows,
           icon_refs=[g["local_path"] for g in glyphs if g["slot"].startswith("lcd-")],
           icon_locale_policy="exact")

    # ---- p8-11 OPERATIONS -------------------------------------------------------------------
    b.chapter("operations", "OPERATIONS", [8, 9, 10, 11])
    b.h("POWER ON/OFF")
    b.figure("power-on-off")
    b.callout("NOTE", P("After Energy Saving Mode is enabled, if the AC or DC power button is turned on and the "
                        "product has no charging or discharging activity or remains in a low-power state for 6 hours, "
                        "the system will automatically turn off the outputs that are in the low-power state.\n"
                        "Definition of low-power state:"),
              UL("AC output power ≤ 25W", "DC output power (USB output + DC 12V port output) ≤ 2W"), variant="note")
    b.h("AC OUTPUT ON/OFF")                                                           # p9
    b.figure("ac-output")
    b.h("DC 12V OUTPUT ON/OFF")
    b.figure("dc-output")
    b.add(P("The product can charge your car battery using the Jackery 12V automobile battery charging cable, which "
            "is sold separately and available on our website."))
    b.callout("CAUTION", UL(
        "The DC 12V port is only compatible with 12V car batteries and not suitable for 24V systems.",
        "Do not start the car while the product is charging the car battery through the DC 12V port, as this may "
        "damage the product.",
        "This feature is intended for emergency use only and cannot charge a dead or damaged car battery."),
        variant="caution")
    b.h("USB OUTPUT ON/OFF")                                                          # p10
    b.figure("usb-output")
    b.add(P("USB-C is USB-PD Power Source 3 (PS3) high-power output port. If the connected user device or accessory "
            "does not meet safety requirements, there may be a fire risk. Before using this port, ensure that the "
            "connected device or accessory has fire safety protection.\n"
            "Only connect the Jackery Explorer 300 to devices or accessories that comply with clauses 6.3, 6.4, and "
            "6.5 of IEC/EN/UL 62368-1 (or other equivalent standards)."))
    b.h("ENERGY SAVING MODE")
    b.add(P("To prevent unnecessary battery consumption caused by forgetting to turn off the output, Energy Saving "
            "Mode is enabled by default. If no device is connected or the connected device's power consumption is "
            "below a certain threshold (AC output ≤ 25W, USB + DC 12V port ≤ 2W ) for 6 hours, the product will "
            "automatically turn off the outputs."),
          P("To turn Energy Saving Mode on or off, press and hold both the AC power button and the main power button "
            "for 3 seconds."))
    b.figure("energy-saving")
    b.callout("Note", UL(
        "When Energy Saving Mode is disabled, the product will not automatically turn off the AC or DC output.",
        "Energy Saving Mode resumes previous state after power-on. Manual switching is required for mode changes."),
        variant="note")
    b.h("LCD SCREEN ON/OFF")                                                          # p11
    b.used_figures.append("lcd-screen")
    groups = [{**pair(state, "state"), "actions": [{**pair(a, "action"), **pair(d, "description")} for a, d in acts]}
              for state, acts in [
        ("LCD Screen", [("Turn on", "Press the Main Power Button or\nwhen the product is charging."),
                        ("Turn off", "Press the Main Power Button."),
                        ("Auto-off", "The LCD screen turns off automatically after 2 minutes of inactivity.")]),
        ("Always-on Display Mode\n(under charging or discharging state)",
         [("Turn on", "Double-click the Main Power Button when the LCD screen is ON."),
          ("Turn off", "Press the Main Power Button."),
          ("Auto-off", "The Always-on Display Mode turns off automatically after 2 hours of inactivity.")]),
    ]]
    b.comp(lcd_mode_component_spec, accessibility_label="LCD SCREEN ON/OFF", groups=groups,
           artwork_ref=b.figures["lcd-screen"]["local_path"], artwork_locale_policy="exact")

    # ---- p11-13 CHARGING ----------------------------------------------------------------------
    b.chapter("charging", "CHARGING", [11, 12, 13])
    b.add(P("**Green energy first:** We advocate to use the green energy first. This product supports two modes of "
            "charging at the same time: solar charging and AC wall charging. When AC wall charging and solar charging "
            "are turned on at the same time, the product will give priority to solar charging and both methods will be "
            "used to charge the battery at the maximum permissible power."),
          P("**Fully charge the product before its first use.**"))
    b.callout("Note", UL(
        "The recommended charging temperature for the product ranges from 32°F to 113°F (0°C to 45°C), and the "
        "discharging temperature ranges from 5°F to 113°F (-15°C to 45°C). Operating the product beyond this "
        "temperature range may restrict its charging and discharging capabilities, or even prevent it from charging "
        "or discharging.",
        "The charging power and battery capacity of the product may vary due to temperature fluctuations."),
        variant="note")
    b.callout("Note", "When the product is charged via the 65W AC Adapter or the USB-C port, the charging icon will "
              "not appear on the LCD screen. Please refer to the battery power indicator and input power displayed on "
              "the LCD to check the charging status.", variant="note")
    b.h("CHARGING VIA 65W AC ADAPTER")                                                # p12
    b.add(P("Connect the included 65W AC adapter to the product’s DC8020 port and plug the adapter into a wall outlet."))
    b.figure("charging-ac")
    b.h("CHARGING VIA USB-C PORT (100W MAX)")
    b.add(P("Charge the product using the USB-C port."))
    b.figure("charging-usbc")
    b.callout("Note", "The USB-C port does not support solar panel input.", variant="note")
    b.h("DC INPUT INDICATOR")
    b.figure("dc-input-led")
    b.comp(reference_table_component_spec, variant="lcd-actions-compact", label="DC INPUT INDICATOR",
           headers=[cell_pair("**LED Status**"), cell_pair("**Description**")],
           rows=[[cell_pair(a), cell_pair(d)] for a, d in [("Solid Blue", "Charging"), ("Solid Green", "Fully charged"),
                                                           ("Off", "No power input")]])
    b.callout("Note", "Observe the DC Input Indicator when charging with a solar panel or car charger.", variant="note")
    b.h("CHARGING VIA SOLAR PANELS (100W MAX)")                                       # p13
    b.add(P("Jackery Explorer 300 has one DC8020 input port and is compatible with the Jackery solar panels."))
    b.figure("charging-solar")
    b.add(P("It is recommended to use the Jackery Solar Panel to charge the Explorer 300. Ensure that the open-circuit "
            "voltage (V_{oc}) of the solar panel falls within the Jackery Explorer 300's DC input voltage range "
            "(16V–28V)."))
    b.callout("CAUTION", UL(
        "Only one solar panel can be connected to the DC8020 input port.",
        "Jackery is not responsible for any damage or loss resulting from the use of third-party solar panels."),
        variant="caution")
    b.h("CHARGING WITH A CAR CHARGER")
    b.add(P("This product can be charged using a 12V car charger. Ensure that the car charger and the 12V car power "
            "outlet provide a good connection."))
    b.figure("charging-car")
    b.callout("CAUTION", UL(
        "Please start the vehicle before charging your power station.",
        "If the vehicle is running on bumpy roads, it is forbidden to use the car charger in case it causes "
        "non-standard operation. The Company will not be responsible for any loss caused by non-standard operation.",
        "Vehicle charging is only applicable to vehicles with 12V DC, not 24V DC. Please do not charge this product "
        "in 24V vehicle to avoid personal injury and property loss."), variant="caution")

    # ---- p14 STORAGE, TROUBLESHOOTING -------------------------------------------------------------
    b.chapter("storage", "STORAGE", [14])
    b.add(P("Store the product in a dry clean place with proper ventilation. Storage temperature and humidity:"),
          UL("1 month: -4°F to 113°F / -20°C to 45°C (0-60%RH)",
             "3 months: 32°F to 113°F / 0°C to 45°C (0-60%RH)",
             "12 months: 32°F to 77°F / 0°C to 25°C (0-60%RH)"),
          P("If this product is stored for a long period of time (3 months - 6 months) with the power depleted, it may "
            "become unchargeable. To prevent this and maintain battery health, it is recommended to check and recharge "
            "the product every three months and perform a full charge and discharge cycle at least once every 6 to 12 "
            "months."))
    b.chapter("troubleshooting", "TROUBLESHOOTING", [14])
    b.add(P("If any of the following fault codes appear, follow the listed corrective actions to resolve the issue. "
            "If fault persists, please contact Jackery Customer Support."))
    restart = pair("Restart the product.", "measures")
    numbered = lambda *items: pair("\n".join(f"{i}. {v}" for i, v in enumerate(items, 1)), "measures")  # noqa: E731
    rows = [{**pair(code, "code"), **restart} for code in ("F0", "F1", "F2", "F3")] + [
        {**pair("F4", "code"), **pair("Connect the product to loads to discharge its battery until the fault "
                                      "disappears.", "measures")},
        {**pair("F5", "code"), **pair("Charge the product via solar panels or AC wall outlet until the fault "
                                      "disappears.", "measures")},
        {**pair("F6", "code"), **numbered(
            "Wait for the grid to normalize before charging the product via AC wall outlet.",
            "Check whether the air intake and exhaust vents are blocked; ensure 30 cm clearance on both side of the "
            "product.",
            "Place the product in a shaded, well-ventilated area where the ambient temperature is below 45°C.",
            "Disconnect all loads from the product, keep it idle and wait until the fault disappears.",
            "Restart the product.")},
        {**pair("F7", "code"), **numbered(
            "Remove all DC inputs from the product.",
            "If you charge the product via a solar panel, check the open-circuit voltage (V_{oc}) of the connected "
            "solar panel. The product allows a maximum DC input voltage of 28V.",
            "Restart the product and keep it idle. Wait until the fault disappears.")},
        {**pair("F8", "code"), **pair("Contact Jackery Customer Support.", "measures")},
        {**pair("F9", "code"), **pair("Remove the load connected to the USB/DC 12V ports of the product. Wait until "
                                      "the fault disappears.", "measures")},
    ]
    b.comp(troubleshooting_component_spec, headers=[pair("Error Code", "content"), pair("Corrective Measures", "content")],
           rows=rows)

    # ---- p15 SPECIFICATIONS ----------------------------------------------------------------------
    b.chapter("specifications", "SPECIFICATIONS", [15])
    usb = f"100W Max, 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A"
    for title, rows in [
        ("GENERAL INFO", [("Product Name", "Jackery Explorer 300"), ("Model No.", "JE-300E-SG"),
                          ("Capacity", "15.2Ah / 19.2V DC (291.84 Wh)"), ("Cell Chemistry", "LiFePO₄"),
                          ("Weight", "About 7.5 lbs / 3.4 kg"), ("Dimensions", "9.06×6.02×7.83 in / 23×15.3×19.9cm"),
                          ("Cycle Life", "4000 cycles to 70%+ capacity")]),
        ("INPUT PORTS", [("1 × USB-C Input", usb), ("1 × DC8020 Input", f"11V-16V{DC}6A Max, 96W Max"),
                         ("", f"16V-28V{DC}6A Max, 100W Max")]),
        ("OUTPUT PORTS", [("2 × AC Output", "120V~60Hz, 2.5A, 300W Max (14°F to 113°F/-10°C to 45°C)"),
                          ("", "120V~60Hz, 2.0A, 200W Max (5°F to 14°F/-15°C to -10°C)"),
                          ("AC Total Output", "300W Rated, 600W Surge peak"), ("1 × USB-C Output", usb),
                          ("1 × USB-A1 Output", f"15W Max, 5V{DC}3A"), ("1 × USB-A2 Output", f"15W Max, 5V{DC}3A"),
                          ("1 × DC 12V Port", f"12V{DC}10A Max")]),
        ("ENVIRONMENTAL OPERATING TEMPERATURE", [("Charge Temperature", "32°F to 113°F / 0°C to 45°C"),
                                                 ("Discharge Temperature", "5°F to 113°F / -15°C to 45°C")]),
    ]:
        b.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows)
    b.add(P("※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."))
    b.callout("Note", "The device's output power will adjust automatically under different ambient temperatures to "
              "ensure safe operation and extend battery life.", variant="note")

    # ---- p16 WARRANTY ----------------------------------------------------------------------------
    b.chapter("warranty", "WARRANTY", [16])
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
        ("Exclusions", blocks(
            "**Jackery's warranty does not apply to:**",
            ["Misused, abused, modified, damaged by accident, or used for anything other than normal consumer use as "
             "authorized in Jackery's current product literature.",
             "Attempted repair by anyone other than an authorized facility.",
             "Any product purchased through an online auction house.",
             "Jackery's warranty does not apply to the battery cell unless the battery cell is fully charged by you "
             "within seven days after you purchase the product and at least once every 6 months thereafter."])),
        ("Interpretation Rights", blocks(
            "Jackery reserves the right to final interpretation of the above customers' after-sales policy.")),
    ]
    for index, (title, body) in enumerate(sections, start=1):
        b.h(title)
        if body is None:
            b.comp(warranty_years_component_spec, title=title, periods=[
                {"number": "3", "unit": "YEARS", "label": "Standard Warranty",
                 **_body(
                     "The standard warranty period for Jackery Explorer 300 is 36 months. In each case, the warranty "
                     "period is measured starting on the date of purchase by the original consumer purchaser. The sales "
                     "receipt from the first consumer purchaser, or other reasonable documentary proof, is required in "
                     "order to establish the start date of the warranty period.")},
                {"number": "2", "unit": "YEARS", "label": "Extended Warranty",
                 **_body(
                     "To activate the Warranty Extension, you must register your product online or contact our customer "
                     "service team at hello@jackery.com to extend the standard warranty runtime.")},
            ])
            continue
        b.comp(warranty_section_component_spec, title=title, section_index=index, blocks=body)

    # ---- p17 back cover: contact -------------------------------------------------------------------
    b.chapter("contact", "JACKERY INC.", [17])
    b.add(P("5310 Bunche Dr., Fremont, CA 94538-8301"),
          P("1-888-502-2236 (US)\nhello@jackery.com\nwww.jackery.com"))
    b.figure("contact-qr")

    problems = b.finish()
    print("chapters", len(b.chapters), "problems", problems)
    return problems


def _body(value: str) -> dict:
    import html
    return {"body_html": "<p>" + html.escape(value) + "</p>", "body_text": value}


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
