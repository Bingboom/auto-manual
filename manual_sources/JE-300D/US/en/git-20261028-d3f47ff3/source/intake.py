"""Write the JE-300D US English semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-300D/US/en/git-20261028-d3f47ff3/source/intake.py``.
It writes ``source/en/content.json``. ``original.pdf`` is outlined (no text
layer), so every English line below is transcribed from 300 dpi renders of the
named physical page and kept as printed. Every printed block maps to a shared
component or plain shared flow (``source_manifest.json:component_map``); no
package class, inline style or plain table. The cover (p1) and contents (p3)
are not Web content.
"""
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import P, UL, Book, blocks, cell_pair, fcc_flow, pair, spec_carrier  # noqa: E402
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
from tools.web.frozen_ai_flow import node, table, text  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
DC = "⎓"  # the print's DC symbol
TIP = ("TIP", "The car charging cable is not included but is available for purchase separately on our website. "
              "For assistance, please contact Jackery Customer Support.")


def inbox_carrier(spec):
    """Shared inbox cards plus the printed TIP strip (JE-1500D US form)."""
    from tools.component_specs.inbox_adapters import web_inbox_projection
    cards = web_inbox_projection(spec)["cards"]
    return [table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                        node("paragraph", [text(c["label"])])], header=False) for c in cards]]),
            table([[node("table_cell", [text(TIP[0])], header=False),
                    node("table_cell", [text(TIP[1])], header=False)]])]


def make() -> list[str]:
    b = Book(SOURCE, "JE-300D", "US", "en", "Jackery Explorer 300D · JE-300D")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731

    # ---- p2 IMPORTANT (the "US" badge marks the language edition) ----------------
    b.chapter("introduction", "IMPORTANT", [2])
    b.add(P("Congratulations on your new Jackery Explorer 300D. Please read this manual carefully before using the "
            "product, particularly the relevant precautions to ensure proper use. Keep this manual in an accessible "
            "place for frequent reference."),
          P("In compliance with laws and regulations, the right of final interpretation of this document and all "
            "related documents of this product resides with the Company."),
          P("Please kindly notice that no further notifications will be given in case of any update, revision or "
            "termination."))

    # ---- p4-5 IMPORTANT SAFETY INFORMATION -----------------------------------------
    b.chapter("safety", "IMPORTANT SAFETY INFORMATION", [4, 5])
    b.callout("WARNING", "**INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS**",
              variant="warning")
    b.callout("WARNING", "**Always follow these basic precautions when using this product.**", variant="warning")
    b.add(UL(
        "Read all the instructions before using the product.",
        "Do not allow children to play with the product. Close supervision of children is necessary when the "
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
         "specified operating temperature ranges :",
         UL("Charging temperature: 32°F to 113°F (0°C to 45°C);",
            "Discharging temperature: 5°F to 113°F (-15°C to 45°C);")),
        ("To ensure proper air circulation, keep the product vents uncovered. The area where the product is used "
         "must have adequate airflow in a cool, dry environment to prevent overheating.",
         UL("Charging in damp or poorly ventilated spaces may cause safety hazards.",
            "Water can cause short circuits or damage to the charger, leading to safety risks.")),
        "Unplug the power cord from a power outlet during a storm.",
        "Immediately turn off the product by pressing the power button if it has fallen, been dropped, or exposed "
        "to vibrations.",
        "Do not charge the product using a damaged or broken charging cord or plug.",
        "Do not use the product to charge any device with a damaged or broken cable or plug.",
        "Always unplug the charging cord by pulling the plug, not the cord, to reduce the risk of damage.",
        "Ensure the product is properly secured when transporting it in a moving vehicle.",
        "DO NOT place the product on the floor or at a height less than 18 inches (457 mm) above the floor during "
        "operation in a workshop or repair facility.",
        "DO NOT use the product's accessories with other devices or equipment.",
        "Solar charge times depend on weather conditions, place your solar panel where it will get as much direct "
        "sunlight as possible.",
    ))
    b.callout("DANGER", "This device is intended for indoor use only (Please place this device in a similar indoor "
              "environment when using it outdoors, e.g. Home RVs, tents, cabins, etc.).\n"
              "* This device is not waterproof or dustproof. Keep away from rain and humid environments during use.",
              variant="danger")
    b.h("USER MAINTENANCE INSTRUCTIONS")                                              # p5
    b.add(P("During the lifecycle of energy storage products, a certain degree of capacity and energy degradation is "
            "expected. As the number of charge and discharge cycles increases and storage time extends, this "
            "degradation will gradually intensify, which is a normal phenomenon consistent with the natural aging of "
            "battery cells."))

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

    # ---- p6 WHAT'S IN THE BOX --------------------------------------------------------------
    b.chapter("in_the_box", "WHAT'S IN THE BOX", [6])
    slots = ("inbox-unit", "inbox-user-manual")
    cards = [{"image_ref": b.figures[slot]["local_path"], "label": b.figures[slot]["caption"],
              "alt": b.figures[slot]["caption"]} for slot in slots]
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="WHAT'S IN THE BOX", cards=cards,
           tip_label=TIP[0], tip_body=TIP[1])

    # ---- p6-7 PRODUCT OVERVIEW ---------------------------------------------------------------
    b.chapter("product_overview", "PRODUCT OVERVIEW", [6, 7])
    b.figure("overview-front")
    b.add(P("**The handle attachments can also be used for adjustable straps (sold separately).**"))  # p7
    b.figure("adjustable-strap")

    # ---- p7-8 LCD DISPLAY -----------------------------------------------------------------
    b.chapter("lcd_display", "LCD DISPLAY", [7, 8])
    b.figure("lcd-display")
    glyphs = load("glyphs.json")
    names = [
        ("1", "Input Power", "Displays the input power in watts."),
        ("2", "USB-C Charging Indicator", "The product is charged via the USB-C port."),
        ("3", "Car Charging Indicator", "The product is charged via the DC Input (DC8020) using DC 12V (car charging)."),
        ("4", "Solar Charging Indicator", "The product is charged via the DC Input (DC8020) using solar panel(s)."),
        ("5", "Battery Power Indicator", "When the product is being charged, the orange circle around the battery "
         "percentage will light up in sequence.\nWhen charging other devices, the orange circle will stay on."),
        ("6", "Remaining Battery Percentage", "Displays the remaining battery percentage."),
        ("7", "Energy Saving Mode", "On: Energy Saving Mode is enabled.\nOff: Energy Saving Mode is disabled."),
        ("8", "High Temperature Indicator", "High temperature protection is triggered. The product may stop "
         "functioning until its temperature returns to the normal operating range."),
        ("8", "Low Temperature Indicator", "Low temperature protection is triggered. The product may stop "
         "functioning until its temperature returns to the normal operating range."),
        ("9", "Fault Code", "A product error has occurred. Please refer to the Troubleshooting section for details."),
        ("10", "Output Power", "Displays the output power in watts."),
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
    b.add(P("The product will automatically shut down only when its battery is depleted."))
    b.h("USB OUTPUT ON/OFF")                                                          # p9
    b.add(P("Once the product is turned on, the USB ports are automatically enabled for power output, allowing you to "
            "charge your devices."))
    b.figure("usb-output")
    b.callout("CAUTION", UL(
        "USB-C1 and USB-C2 are USB-PD Power Source 3 (PS3) high-power output ports. If the connected user device or "
        "accessory does not meet safety requirements, there may be a fire risk. Before using these ports, ensure that "
        "the connected device or accessory has fire safety protection.",
        "Only connect the Jackery Explorer 300D to devices or accessories that comply with clauses 6.3, 6.4, and 6.5 "
        "of IEC/EN/UL 62368-1 (or other equivalent standards).",
        "To obtain maximum output power, use the official Jackery USB-C to USB-C 5A cable (20V DC/5A, 100W; "
        "28V DC/5A, 140W)."), variant="caution")
    b.h("DC 12V OUTPUT ON/OFF")
    b.add(P("**Prerequisite:** The product is turned on."))
    b.figure("dc-output")
    b.add(P("* The product can charge your car battery using the Jackery 12V automobile battery charging cable, which "
            "is sold separately and available on our website."))
    b.callout("CAUTION", UL(
        "The DC 12V outlet (cigarette lighter port) is only compatible with 12V car batteries and not suitable for "
        "24V systems.",
        "Do not start the car while the product is charging the car battery through the 12V DC output port "
        "(cigarette lighter port), as this may damage the product.",
        "This feature is intended for emergency use only and cannot charge a dead or damaged car battery."),
        variant="caution")
    b.h("ENERGY SAVING MODE")                                                         # p10
    b.add(P("To prevent unnecessary battery consumption from forgetting to turn off the output, the product enables "
            "Energy Saving Mode by default. If no device is connected or the connected device's power consumption is "
            "below 2W for 6 hours, the product will automatically turn off all outputs and then power off.\n"
            "To disable the energy saving mode, press the main power button three times. The product will not "
            "automatically turn off the output."))
    b.figure("energy-saving")
    b.callout("NOTE", "Energy Saving Mode resumes previous state after power-on. Manual switching is required for "
              "mode changes.", variant="note")
    b.h("LED LIGHT ON/OFF")
    b.add(P("The LED light has two modes: Light mode and SOS mode. The default setting is Light mode. In any mode, "
            "press and hold the LED light button to turn off the light."))
    b.figure("led-light")
    b.h("LCD SCREEN ON/OFF")                                                          # p11
    b.used_figures.append("lcd-screen")
    groups = [{**pair(state, "state"), "actions": [{**pair(a, "action"), **pair(d, "description")} for a, d in acts]}
              for state, acts in [
        ("LCD Screen", [("Turn on", "Press the Main Power Button or when the product is charging."),
                        ("Turn off", "Press the Main Power Button."),
                        ("Auto-off", "The LCD turns off automatically and enters sleep mode after 2 minutes of "
                                     "inactivity.")]),
        ("Always-on Display Mode (under charging or discharging state)",
         [("Turn on", "Double-press the Main Power Button when the LCD screen is ON."),
          ("Turn off", "Press the Main Power Button."),
          ("Auto-off", "The Always-on Display Mode turns off automatically after 2 hours of inactivity.")]),
    ]]
    b.comp(lcd_mode_component_spec, accessibility_label="LCD SCREEN ON/OFF", groups=groups,
           artwork_ref=b.figures["lcd-screen"]["local_path"], artwork_locale_policy="exact")

    # ---- p11-13 CHARGING ----------------------------------------------------------------------
    b.chapter("charging", "CHARGING", [11, 12, 13])
    b.add(P("**Green energy first:** We advocate to use the green energy first. This product supports two modes of "
            "charging at the same time: solar charging and USB-C charging. When USB-C charging and solar charging are "
            "turned on at the same time, the product will give priority to solar charging and both methods will be "
            "used to charge the battery at the maximum permissible power."),
          P("**Fully charge the product before its first use.**"))
    b.callout("NOTE", UL(
        "The recommended charging temperature for the product ranges from 32°F to 113°F (0°C to 45°C), and the "
        "discharging temperature ranges from 5°F to 113°F (-15°C to 45°C). Operating the product beyond this "
        "temperature range may restrict its charging and discharging capabilities, or even prevent it from charging "
        "or discharging.",
        "The charging power and battery capacity of the product may vary due to temperature fluctuations."),
        variant="note")
    b.h("USB-C CHARGING (140W MAX)")                                                  # p12
    b.add(P("Prepare a wall charger. Remove the two-in-one carry handle, which is also a USB-C cable. Connect it to the "
            "product’s USB-C1 port and a power outlet."))
    b.figure("charging-usbc")
    b.callout("CAUTION", "When charging through the USB-C port, this product supports up to 140W, which requires a PD "
              "charger and cable that both support 140W.", variant="caution")
    b.h("SOLAR CHARGING (100W MAX)")
    b.add(P("The Jackery Explorer 300D has one DC8020 input port, which supports direct connection of a solar panel."))
    b.figure("charging-solar")
    b.add(P("It is recommended to use a Jackery solar panel to charge the product. Ensure that the open-circuit "
            "voltage (V_{oc}) of the solar panel falls within the Jackery Explorer 300D's DC input voltage range "
            "(16V–28V). Jackery is not responsible for any damage or loss resulting from the use of third-party "
            "solar panels."))
    b.h("CAR CHARGING (96W MAX)")                                                     # p13
    b.add(P("This product can be charged using a 12V car charger. Ensure that the car charger and the car cigarette "
            "lighter provide a good connection."))
    b.figure("charging-car")
    b.add(P("* The car charging cable is sold separately."))
    b.callout("CAUTION", UL(
        "Please start the vehicle before charging your power station.",
        "If the vehicle is running on bumpy roads, it is forbidden to use the car charger in case it causes "
        "non-standard operation. The Company will not be responsible for any loss caused by non-standard operation.",
        "Vehicle charging is only applicable to vehicles with 12V DC, not 24V DC. Please do not charge this product "
        "in 24V vehicle to avoid personal injury and property loss."), variant="caution")

    # ---- p14 STORAGE, TROUBLESHOOTING -------------------------------------------------------------
    b.chapter("storage", "STORAGE", [14])
    b.add(P("Store the product in a dry clean place with proper ventilation. Storage temperature and humidity:"),
          UL("1 month: -20°C to 45°C (0-60%RH)",
             "3 months: 0°C to 45°C (0-60%RH)",
             "12 months: 0°C to 25°C (0-60%RH)"),
          P("If this product is stored for a long period of time (3 months - 6 months) with the power depleted, it may "
            "become unchargeable. To prevent this and maintain battery health, it is recommended to check and recharge "
            "the product every three months and perform a full charge and discharge cycle at least once every 6 to 12 "
            "months."))
    b.chapter("troubleshooting", "TROUBLESHOOTING", [14])
    b.add(P("If any of the following fault codes appear, follow the listed corrective actions to resolve the issue. "
            "If fault persists, please contact Jackery Customer Support."))
    restart = pair("Restart the product.", "measures")
    support = pair("Contact Jackery Customer Support.", "measures")
    numbered = lambda *items: pair("\n".join(f"{i}. {v}" for i, v in enumerate(items, 1)), "measures")  # noqa: E731
    rows = [
        {**pair("F0", "code"), **restart},
        {**pair("F1", "code"), **support},
        {**pair("F2", "code"), **support},
        {**pair("F3", "code"), **restart},
        {**pair("F4", "code"), **pair("Connect the product to loads to discharge its battery until the fault "
                                      "disappears.", "measures")},
        {**pair("F5", "code"), **pair("Charge the product via USB-C or solar panel until the fault disappears.",
                                      "measures")},
        {**pair("F6", "code"), **support},
        {**pair("F7", "code"), **numbered(
            "Remove all DC inputs from the product.",
            "If you charge the product via a solar panel, check the open-circuited voltage (V_{oc}) of the connected "
            "solar panel.The product allows a maximum DC input voltage of 28V.",
            "Restart the product and keep it idle. Wait until the fault disappears.")},
        {**pair("F8", "code"), **support},
        {**pair("F9", "code"), **pair("Remove the load connected to the DC 12V/USB ports of the product. Wait until "
                                      "the fault disappears.", "measures")},
    ]
    b.comp(troubleshooting_component_spec, headers=[pair("Error Code", "content"), pair("Corrective Measures", "content")],
           rows=rows)

    # ---- p15-16 SPECIFICATIONS -------------------------------------------------------------------
    b.chapter("specifications", "SPECIFICATIONS", [15, 16])
    c1 = f"140W Max, 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A, 28V{DC}5A"
    for title, rows in [
        ("GENERAL INFO", [("Product Name", "Jackery Explorer 300D"), ("Model No.", "JE-300D"),
                          ("Capacity", "15Ah / 19.2V DC (288 Wh)"), ("Cell Chemistry", "LiFePO₄"),
                          ("Weight", "About 5.51 lbs/2.5 kg"), ("Dimensions", "4.67×4.73×7.20 in / 11.86×12.02×18.3 cm"),
                          ("Cycle Life", "4000 cycles to 70%+ capacity")]),
        ("INPUT PORTS", [("1 × USB-C Input", f"C1: 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A, 28V{DC}5A, "
                                             "140W Max"),
                         ("1 × DC8020 Port", f"PV: 16-28V{DC}6A Max, 100W Max"),
                         ("", f"Car: 11-16V{DC}6A Max, 96W Max")]),
        ("OUTPUT PORTS", [("3 × USB-C Port", "C1: " + c1), ("", "C2: " + c1),
                          ("", f"C3: 65W Max, 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}3.25A"),
                          ("1× USB-A Port", f"15W Max, 5V{DC}3A"), ("1× DC 12V Port", f"12V{DC}10A Max")]),
        ("ENVIRONMENTAL OPERATING TEMPERATURE", [("Charge Temperature", "32°F to 113°F / 0°C to 45°C"),
                                                 ("Discharge Temperature", "5°F to 113°F / -15°C to 45°C")]),
    ]:
        b.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows)
    b.h("Multi-Port Output Combinations")
    for title, first, rows in [
        ("1-Port Output", "Port Used", [("USB-C1", "140W"), ("USB-C2", "140W"), ("USB-C3", "65W"), ("USB-A", "15W"),
                                        ("DC 12V Port", "120W")]),
        ("2-Port Output", "Combination", [
            ("USB-C1 + USB-C2", "140W + 140W"), ("USB-C1 + USB-C3", "140W + 65W"), ("USB-C1 + USB-A", "140W + 15W"),
            ("USB-C1 + DC 12V Port", "140W + 120W"), ("USB-C2 + USB-C3", "140W + 65W"),
            ("USB-C2 + USB-A", "140W + 15W"), ("USB-C2 + DC 12V Port", "140W + 120W"),
            ("USB-C3 + USB-A", "65W + 15W"), ("USB-C3 + DC 12V Port", "65W + 120W"),
            ("USB-A + DC 12V Port", "15W + 120W")]),
        ("3-Port Output", "Combination", [
            ("USB-C1 + USB-C2 + USB-C3", "140W + 140W + 65W"), ("USB-C1 + USB-C2 + USB-A", "140W + 140W + 15W"),
            ("USB-C1 + USB-C2 + DC 12V Port", "100W + 100W + 120W"), ("USB-C1 + USB-C3 + USB-A", "140W + 65W + 15W"),
            ("USB-C1 + USB-C3 + DC 12V Port", "140W + 65W + 120W"), ("USB-C1 + USB-A + DC 12V Port", "140W + 15W + 120W"),
            ("USB-C2 + USB-C3 + USB-A", "140W + 65W + 15W"), ("USB-C2 + USB-C3 + DC 12V Port", "140W + 65W + 120W"),
            ("USB-C2 + USB-A + DC 12V Port", "140W + 15W + 120W"), ("USB-C3 + USB-A + DC 12V Port", "65W + 15W + 120W")]),
        ("4-Port Output", "Combination", [
            ("USB-C1 + USB-C2 + USB-C3 + USB-A", "140W + 65W + 65W + 15W"),
            ("USB-C1 + USB-C2 + USB-C3 + DC 12V Port", "100W + 65W + 30W + 120W"),
            ("USB-C1 + USB-C2 + USB-A + DC 12V Port", "100W + 65W + 15W + 120W"),
            ("USB-C1 + USB-C3 + USB-A + DC 12V Port", "100W + 65W + 15W + 120W"),
            ("USB-C2 + USB-C3 + USB-A + DC 12V Port", "100W + 65W + 15W + 120W")]),
        ("5-Port Output", "All Ports Active", [
            ("USB-C1 + USB-C2 + USB-C3 + USB-A + DC 12V Port", "65W + 65W + 30W + 15W + 120W")]),
    ]:
        b.h(title, level=4)
        b.comp(reference_table_component_spec, variant="lcd-actions-compact", label=title,
               headers=[cell_pair(first), cell_pair("Max Output")],
               rows=[[cell_pair(a), cell_pair(v)] for a, v in rows])
        if title == "1-Port Output":
            b.add(P("* In some combinations, USB-C1/2/3 may be limited depending on main port priority."))
    b.add(P("※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."),
          P("When devices are connected to the high-power ports, the output power may be automatically adjusted by the "
            "product's temperature protection mechanism. This is normal operation and does not indicate a malfunction. "
            "There is no need for concern."))

    # ---- p17 WARRANTY ----------------------------------------------------------------------------
    b.chapter("warranty", "WARRANTY", [17])
    b.comp(warranty_lead_component_spec, accessibility_label="WARRANTY",
           lead_html="<strong>We only provide our warranty to customers who purchase from the official Jackery website, "
                     "Jackery-branded third-party platforms, or local authorized dealers.</strong>",
           local_note_html="*Warranty period and details may vary according to local laws, regulations, and authorized "
                           "dealers.")
    sections = [
        ("Limited Warranty", blocks(
            "Jackery warrants to the original consumer purchaser that the Jackery product will be free from defects "
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
            "Jackery's warranty does not apply to:",
            ["Misused, abused, modified, damaged by accident, or used for anything other than normal consumer use as "
             "authorized in Jackery's current product literature.",
             "Attempted repair by anyone other than an authorized facility.",
             "Any product purchased through an online auction house.",
             "Jackery's warranty does not apply to the battery cell unless the battery cell is fully charged by you "
             "within seven days after you purchase the product and at least once every 6 months thereafter."])),
        ("Interpretation Rights", blocks(
            "Jackery reserves the right to final interpretation of the above customer after-sales policy.")),
        ("Customer Support", blocks(
            "hello@jackery.com (US&CA)\nhello.sg@jackery.com (Singapore)\nhello.my@jackery.com (Philippines)")),
    ]
    for index, (title, body) in enumerate(sections, start=1):
        b.h(title)
        if body is None:
            b.comp(warranty_years_component_spec, title=title, periods=[
                {"number": "3", "unit": "YEARS", "label": "Standard Warranty",
                 **_body(
                     "The standard warranty period for Jackery Explorer 300D is 36 months. In each case, the warranty "
                     "period is measured starting on the date of purchase by the original consumer purchaser. The sales "
                     "receipt from the first consumer purchaser, or other reasonable documentary proof, is required in "
                     "order to establish the start date of the warranty period.")},
                {"number": "2", "unit": "YEARS", "label": "Extended Warranty",
                 **_body(
                     "To activate the Warranty Extension, you must register your product online or contact our customer "
                     "service team to extend the standard warranty runtime.")},
            ])
            continue
        b.comp(warranty_section_component_spec, title=title, section_index=index, blocks=body)

    # ---- p18 back cover: contact -------------------------------------------------------------------
    b.chapter("contact", "CONTACT US", [18])
    b.h("Hong Kong Hello Tech Energy Co., Limited")
    b.add(P("FLAT/RM 08, 15/F, Witty Commercial Building,\n1A-1L Tung Choi Street, Kowloon, Hong Kong"))
    b.h("JACKERY INC.")
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
