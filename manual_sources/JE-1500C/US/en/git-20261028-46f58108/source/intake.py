"""Write the JE-1500C US English semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-1500C/US/en/git-20261028-46f58108/source/intake.py``.
It writes ``source/en/content.json``. ``original.pdf`` is outlined (no text
layer), so every English line below is transcribed from 220-400 dpi renders of the
named physical page and kept as printed. Every printed block maps to a shared
component or plain shared flow (``source_manifest.json:component_map``); no package
class, inline style or plain table. The cover (p1) and contents (p3) are not Web content.
"""
from html import escape
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import OL, P, UL, Book, blocks, cell_pair, fcc_flow, inbox_carrier, pair, panel, spec_carrier  # noqa: E402
from tools.component_specs.app import app_download_component_spec, app_inline_control_component_spec  # noqa: E402
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
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒"


def make() -> list[str]:
    b = Book(SOURCE, "JE-1500C", "US", "en", "Jackery Explorer 1500 Ultra · JE-1500C")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731

    # ---- p2 IMPORTANT (the "EN" badge marks the language edition) ----------------
    b.chapter("introduction", "IMPORTANT", [2])
    b.add(P("Congratulations on your new Jackery Explorer 1500 Ultra. Please read this manual carefully before "
            "using the product, particularly the relevant precautions to ensure proper use. Keep this manual in an "
            "accessible place for frequent reference."),
          P("In compliance with laws and regulations, the right of final interpretation of this document and all "
            "related documents of this product resides with the Company."),
          P("Please kindly notice that no further notifications will be given in case of any update, revision or "
            "termination."))

    # ---- p4-5 IMPORTANT SAFETY INFORMATION (printed 01-02) -------------------------
    b.chapter("safety", "IMPORTANT SAFETY INFORMATION", [4, 5])
    b.callout("WARNING", "**INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS**",
              variant="warning")
    b.callout("WARNING", "**Always follow these basic precautions when using this product.**", variant="warning")
    b.add(UL(
        "Read all the instructions before using the product.",
        "Please ensure that this device maintains a distance of at least 20cm from the human body during use.",
        "Do not allow children to play on the product. Close supervision of children is necessary when the product "
        "is used near children.",
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
         UL("Charging temperature: 32°F to 113°F (0°C to 45°C )",
            "Discharging temperature: 5°F to 113°F (-15°C to 45°C )")),
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
        "DO NOT place the product on the floor or at a height less than 18 inches (457 mm) above the floor during "
        "operation in a workshop or repair facility.",
        "DO NOT use the product's accessories with other devices or equipment.",
        "Solar charge time depends on weather conditions, place your solar panel where it will get as much direct "
        "sunlight as possible.",
    ))
    b.callout("DANGER", "**This device is intended for indoor use only (Please place this device in a similar "      # p5
              "indoor environment when using it outdoors, e.g. Home RVs, tents, cabins, etc.).\n"
              "※ This device is not waterproof or dustproof. Keep away from rain and humid environments during use.**",
              variant="danger")
    b.h("USER MAINTENANCE INSTRUCTIONS")
    b.add(P("During the lifecycle of energy storage products, a certain degree of capacity and energy degradation is "
            "expected. As the number of charge and discharge cycles increases and storage time extends, this "
            "degradation will gradually intensify, which is a normal phenomenon consistent with the natural aging of "
            "battery cells."))

    # ---- p5-6 MEANING OF SYMBOLS, FCC (printed 02-03) ------------------------------
    b.chapter("symbols", "MEANING OF SYMBOLS", [5, 6])
    headers = [pair("Symbol", "content"), pair("Meaning", "content")]
    rows = [{"label": label, "show_icon": True, **pair(meaning, "meaning")} for label, meaning in [
        ("WARNING", "Hazardous practices that may result in severe injury, death, and/or property damage."),
        ("CAUTION", "Hazardous practices that may result in personal injury and/or property damage."),
        ("NOTE", "Hazardous practices that may result in equipment damage, data loss, performance deterioration, "
                 "or unanticipated results."),
        ("TIP", "Supplements the important information or operation tips in the text."),
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
    opening = ("This device complies with part 15 of the FCC Rules. Operation is subject to the following two "  # p6
               "conditions: (1) This device may not cause harmful interference, and (2) this device must accept any "
               "interference received, including interference that may cause undesired operation.")
    left = [
        "NOTE: This equipment has been tested and found to comply with the limits for a Class B digital device, "
        "pursuant to part 15 of the FCC Rules.",
        "These limits are designed to provide reasonable protection against harmful interference in a residential "
        "installation. This equipment generates, uses and can radiate radio frequency energy and, if not installed "
        "and used in accordance with the instructions, may cause harmful interference to communications. However, "
        "there is no guarantee that radio interference will not occur in a particular installation.",
    ]
    lead = ("If this equipment does cause harmful interference to radio or television reception, which can be "
            "determined by turning the equipment off and on, the user is encouraged to try to correct the interference "
            "by one or more of the following measures:")
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
        right_blocks=[paragraph(lead), {"kind": "list", "items": measures}, paragraph(modification)],
        source_ref=f"transcribed-pdf/symbols/{b.serial}", language="en", mark_asset_ref="assets/fcc_mark.svg")
    b.add(fcc_flow(fcc, opening, [*left, lead, " ".join("• " + m for m in measures), modification]))

    # ---- p6 WHAT'S IN THE BOX (printed 03) ------------------------------------------
    b.chapter("in_the_box", "WHAT'S IN THE BOX", [6])
    slots = ("inbox-unit", "inbox-ac-cable", "inbox-user-manual")
    cards = [{"image_ref": b.figures[s]["local_path"], "label": b.figures[s]["caption"], "alt": b.figures[s]["caption"]}
             for s in slots]
    b.used_figures += list(slots)
    tip_body = ("The car charging cable is not included but is available for purchase separately on our website. "
                "For assistance, please contact Jackery Customer Support.")

    def inbox_with_tip(spec):
        return [*inbox_carrier(spec), table([[node("table_cell", [text("TIP")], header=False),
                                              node("table_cell", [text(tip_body)], header=False)]])]
    b.comp(inbox_component_spec, inbox_with_tip, accessibility_label="WHAT'S IN THE BOX", cards=cards,
           tip_label="TIP", tip_body=tip_body)

    # ---- p7 PRODUCT OVERVIEW (printed 04) --------------------------------------------
    b.chapter("product_overview", "PRODUCT OVERVIEW", [7])
    b.h("FRONT VIEW")
    b.figure("overview-front")
    b.figure("overview-ac-total")

    # ---- p8-9 LCD DISPLAY (printed 05-06) ---------------------------------------------
    b.chapter("lcd_display", "LCD DISPLAY", [8, 9])
    b.figure("lcd-map")
    glyphs = load("glyphs.json")
    names = [
        (1, "Wi-Fi", "**On:** Wi-Fi connected.\n**Blink:** Ready to connect to Wi-Fi.\n**Off:** Wi-Fi disconnected."),
        (2, "Bluetooth", "**On:** Bluetooth connected.\n**Blink:** Ready to connect to Bluetooth.\n"
                         "**Off:** Bluetooth disconnected."),
        (3, "Quiet Charging Mode", "**On:** The noise during charging is significantly minimized, while the charging "
         "power is reduced and the charging speed slows down.\n**Off:** Quiet Charging Mode is disabled.\n"
         "Enable/disable this feature in the Jackery App."),
        (4, "Battery Saving Mode", "**On:** Limits the maximum usable battery capacity to extend battery life.\n"
         "**Off:** Battery Saving Mode is disabled.\nEnable/disable this feature in the Jackery App."),
        (5, "Charging Plan", "Customize the charging time of the Jackery Explorer 1500 Ultra. Suitable for situations "
         "with fluctuating electricity prices, it allows for charging plans based on peak and off-peak electricity "
         "times, reducing electricity costs (Please set in the Jackery App)."),
        (6, "Self-powered Mode", "Maximizes the use of solar energy and reduces reliance on grid electricity by "
         "prioritizing stored solar energy, reducing electricity costs (please enable/disable this feature in the "
         "app). The power station must be connected to both solar panels and the grid simultaneously, with load "
         "power limited by bypass power."),
        (7, "UPS", "**On:** The product is in bypass mode, and the switchover time from grid power to the internal "
         "battery is 20 ms.\n**Off:** The product is not in bypass mode."),
        (8, "AC Power Indicator", "The AC output (pure sine wave) is on."),
        (9, "Output Voltage and Frequency", "Displays the output voltage and frequency."),                    # p9
        (10, "Input Power", "Displays the input power in watts."),
        (11, "Remaining Charge Time", "Displays the remaining charging time."),
        (12, "AC Wall Charging Indicator", "The product is charged via the AC Input using grid power."),
        (13, "Car Charging Indicator", "The product is charged via the DC Input (DC8020) using DC 12V (car charging)."),
        (14, "Solar Charging Indicator", "The product is charged via the DC Input (DC8020) using solar panel(s)."),
        (15, "Battery Power Indicator", "When the product is being charged, the orange circle around the battery "
         "percentage will light up in sequence.\nWhen charging other devices, the orange circle will stay on."),
        (16, "Low Battery Indicator", "**On:** The battery level is below 20%.\n**Blink:** The battery level is below "
         "5%.\n**Off:** The battery level is above 20% or the product is charging."),
        (17, "Remaining Battery Percentage", "Displays the remaining battery percentage."),
        (18, "Fault Code", "A product error has occurred. Please refer to the Troubleshooting section for details."),
        (19, "High Temperature Indicator", "High temperature protection is triggered. The product may stop "
         "functioning until its temperature returns to the normal operating range."),
        (19, "Low Temperature Indicator", "Low temperature protection is triggered. The product may stop "
         "functioning until its temperature returns to the normal operating range."),
        (20, "Energy Saving Mode", "**On:** Energy Saving Mode is enabled.\n**Off:** Energy Saving Mode is disabled."),
        (21, "Output Power", "Displays the output power in watts."),
        (22, "Remaining Discharge Time", "Displays the remaining discharging time."),
    ]
    rows = [{**pair(CIRCLED[number - 1], "number"), **pair(name, "name"), **pair(description, "description"),
             "icon_alt": name, "asset_index": index}
            for index, (number, name, description) in enumerate(names)]
    b.comp(lcd_icon_component_spec, accessibility_label="LCD DISPLAY", rows=rows,
           icon_refs=[g["local_path"] for g in glyphs if g["slot"].startswith("lcd-")],
           icon_locale_policy="exact")

    # ---- p10-12 OPERATIONS (printed 07-09) ---------------------------------------------
    b.chapter("operations", "OPERATIONS", [10, 11, 12])
    b.h("POWER ON/OFF")
    b.figure("power-on-off")
    b.add(panel("**Default standby time:** 2 hours",
                "The product will automatically shut down after 2 hours if there is no charging, no AC output, and "
                "the combined output of the DC 12V port and USB ports is less than 3W.\n"
                "*The standby time can be set in the Jackery App."))
    b.callout("NOTE", "When Energy Saving Mode is enabled, the product will automatically shut down after 12 hours if "
              "both the Main Power Button and the AC Power Button are turned on, but the product is neither charging "
              "nor discharging. The shutdown time can be set in the Jackery App.", variant="note")
    b.h("AC OUTPUT ON/OFF")
    b.add(panel("**Prerequisite:** The product is turned on."))
    b.figure("ac-output")
    b.h("DC 12V/USB OUTPUT")                                                            # p11
    b.add(panel("**Prerequisite:**  The product is turned on."))
    b.figure("dc-usb-output")
    b.add(P("The product can charge your car battery using the Jackery 12V automobile battery charging cable, which "
            "is sold separately and available on our website."))
    b.callout("CAUTION:", UL(
        "The DC 12V port is only compatible with 12V car batteries and not suitable for 24V systems.",
        "Do not start the car while the product is charging the car battery through the 12V DC output port, as this "
        "may damage the product.",
        "This feature is intended for emergency use only and cannot charge a dead or damaged car battery."),
        variant="caution")
    b.h("ENERGY SAVING MODE")
    b.add(P("To prevent unnecessary battery consumption from forgetting to turn off the output, the product enables "
            "Energy Saving Mode by default.\n"
            "When AC Power Button is turned on, the Energy Saving Mode icon will be displayed on the LCD screen.\n"
            " If no device is connected or the connected device's power consumption is below a certain threshold "
            "(AC Output ≤ 25W), the device will automatically turn off all outputs after 12 hours."),
          P("**On/Off:** Press and hold both the AC Power Button and Main Power Button for more than 3 seconds."),
          P("Please set the Energy Saving Mode duration in the Jackery App."))
    b.figure("energy-saving")                                                           # p12
    b.callout("NOTE", UL(
        "When Energy Saving Mode is disabled, the product will not automatically turn off the AC or DC output.",
        "Energy Saving Mode resumes previous state after power-on. Manual switching is required for mode changes."),
        variant="note")
    b.callout("WARNING", "When Energy Saving Mode is enabled, the product automatically turns off the AC output if "
              "the connected device’s power consumption remains low for the configured period. When powering devices "
              "that require continuous power, such as refrigerators, routers, security cameras, or aquarium air pumps, "
              "we recommend turning off Energy Saving Mode to prevent unexpected power loss from interrupting their "
              "operation.", variant="warning")
    b.h("LCD SCREEN ON/OFF")
    b.used_figures.append("lcd-screen")
    groups = [{**pair(state, "state"), "actions": [{**pair(a, "action"), **pair(d, "description")} for a, d in acts]}
              for state, acts in [
        ("Screen stays on for 2 minutes",
         [("Turn on", "Press the Main Power Button or when the product is charging."),
          ("Turn off", "Press the Main Power Button."),
          ("Auto-off", "The LCD turns off automatically and enters sleep mode after 2 minutes.")]),
        ("Always-on Display Mode\n (under charging or discharging state)",
         [("Turn on", "Double-press the Main Power Button when the LCD screen is ON."),
          ("Turn off", "Press the Main Power Button."),
          ("Auto-off", "In Always-on Display Mode, the LCD screen will automatically turn off after 2 hours if there "
                       "is no charging, no AC output, and the combined output of the DC 12V port and USB ports is less "
                       "than 3W.")]),
    ]]
    b.comp(lcd_mode_component_spec, accessibility_label="LCD SCREEN ON/OFF", groups=groups,
           artwork_ref=b.figures["lcd-screen"]["local_path"], artwork_locale_policy="exact")
    b.h("BUTTON OPERATIONS")
    # Two printed rows: the shared key-combination table needs three, so the shared
    # reference table carries the printed copy (button names; the clock pictogram is "3s").
    b.comp(reference_table_component_spec, variant="lcd-actions", label="BUTTON OPERATIONS",
           headers=[cell_pair("**Buttons**"), cell_pair("**Operation**"), cell_pair("**Function**")],
           rows=[[cell_pair(a), cell_pair(o), cell_pair(f)] for a, o, f in [
               ("Main Power Button + AC Power Button", "3s\nPress and hold both for 3s",
                "Turn on/off the Energy Saving Mode"),
               ("Main Power Button", "Press and hold for 3s to turn off the product, then keep holding for 10s.",
                "Reset the product")]])

    # ---- p13 UNINTERRUPTIBLE POWER SUPPLY (UPS) (printed 10) -----------------------------
    b.chapter("ups", "UNINTERRUPTIBLE POWER SUPPLY (UPS)", [13])
    b.add(P("Connect the product to a wall outlet with the AC charging cable, then press the AC output button and power "
            "your appliances at the same time.\n"
            "An uninterruptible power supply (UPS) is a type of continual power system that provides automated backup "
            "electric power to a load when the mains grid power fails.\n"
            "In the event of a sudden loss of grid power, the Explorer 1500 Ultra will automatically switch to stored "
            "power within 20 ms to keep your appliances running.\n"
            "In UPS mode, the unit's peak output reaches 1440W before power outages. As simultaneous "
            "charging/discharging is enabled in Bypass Mode, the actual output power is lower than the rated output "
            "power in this mode but returns to rated output power during outages."))
    b.add(panel("**Prerequisite:** The product is turned on."))
    b.figure("ups")
    b.callout("WARNING", P("Do not use this product for applications such as data servers or medical devices, where a "
                           "malfunction could endanger life or cause significant property damage.\n"
                           "For the following equipment, a loss of power supply during use could cause serious harm "
                           "to personal safety or property:"),
              UL("Medical devices and other equipment closely related to life safety.",
                 "Critical equipment such as social infrastructure and public services.",
                 "Business-critical enterprise equipment, etc."),
              P("Individuals who wear a cardiac pacemaker (pacemaker implant recipients)\nmust not use this product."),
              variant="warning")
    b.callout("CAUTION", UL(
        "This product does not support 0 ms switching. Do not connect it to equipment that requires an uninterrupted "
        "power supply, such as data servers or workstations.",
        "Before use, please test compatibility with your device multiple times.",
        "It is recommended to connect one device at a time. Do not use multiple devices simultaneously, as this may "
        "trigger overload protection.",
        "The UPS function works only when a single unit is connected directly to a wall outlet.Do not connect "
        "multiple portable power stations in series (cascade connection). In a cascaded setup, the UPS function will "
        "not operate: the unit may fail to switch over during a power outage, causing connected devices to shut down."),
        variant="caution")

    # ---- p13-15 CHARGING (printed 10-12) ---------------------------------------------------
    b.chapter("charging", "CHARGING", [13, 14, 15])
    b.add(P("**Green energy first:** We advocate to use the green energy first. This product supports two modes of "
            "charging at the same time: solar charging and AC wall charging. When AC wall charging and solar charging "
            "are turned on at the same time, the product will give priority to solar charging and both methods will be "
            "used to charge the battery at the maximum permissible power."),
          P("**Fully charge the product before its first use.**"))
    b.callout("NOTE", UL(
        "The recommended charging temperature for the product ranges from 32°F to 113°F (0°C to 45°C ), and the "
        "discharging temperature ranges from 5°F to 113°F (-15°C to 45°C ). Operating the product beyond this "
        "temperature range may restrict its charging and discharging capabilities, or even prevent it from charging "
        "or discharging.",
        "The charging power and battery capacity of the product may vary due to temperature fluctuations. When the "
        "ambient temperature ranges from 5°F to 14°F (-15°C to -10°C), the maximum output power decreases to 1000W."),
        variant="note")
    b.h("CHARGING VIA AC WALL OUTLET")                                                  # p14
    b.add(P("Connect the AC charging cable to the AC input port of the product and a wall outlet."))
    b.figure("charging-ac")
    b.callout("CAUTION", "Make sure the AC charging cable is fully and securely plugged into the AC input port. An "
              "incomplete connection may cause unstable current, overheating, poor contact, or device malfunction.",
              variant="caution")
    b.h("CHARGING VIA SOLAR PANELS")
    b.add(P("Jackery Explorer 1500 Ultra has two DC8020 input ports and is compatible with the Jackery solar panels. If "
            "one DC8020 input port needs to connect two solar panels simultaneously, please refer to the figure below "
            "for charging through the solar panel connector (sold separately, not included as standard)."))
    b.figure("charging-solar")
    b.figure("charging-solar-connector")
    b.add(P("It is recommended to use the Jackery Solar Panel to charge the Explorer 1500 Ultra. Ensure that the "  # p15
            "open-circuit voltage (Voc) of the solar panel falls within the Jackery Explorer 1500 Ultra's DC input "
            "voltage range (16V–60V). Jackery is not responsible for any losses caused by using solar panels from "
            "other brands."))
    b.callout("CAUTION", "One DC8020 input port can be connected to at most two solar panels.", variant="caution")
    b.callout("CAUTION", P("Ensure that the input voltage for both DC input ports is the same. Failure to do so may "
                           "damage the product. For example:"),
              UL("It is recommended to use the same model of Jackery solar panels and the same number of panels when "
                 "connecting solar panels to both DC8020 Input ports.",
                 "Do not charge the product using both a car charger and a solar panel simultaneously. Doing so may "
                 "blow the car fuse or result in charging failure."),
              variant="caution")
    b.h("CHARGING WITH A CAR CHARGER")
    b.add(P("This product can be charged using a 12V car charger. Ensure that the car charger and the 12V car power "
            "outlet provide a good connection."))
    b.figure("charging-car")
    b.add(panel("*The car charging cable is sold separately."))
    b.callout("CAUTION", UL(
        "Please start the vehicle before charging your power station.",
        "If the vehicle is running on bumpy roads, it is forbidden to use the car charger in case it causes "
        "non-standard operation. The Company will not be responsible for any loss caused by non-standard operation.",
        "Vehicle charging is only applicable to vehicles with 12V DC, not 24V DC. Please do not charge this product in "
        "24V vehicle to avoid personal injury and property loss."), variant="caution")

    # ---- p16 BOTTOM CLEANING (printed 13) ------------------------------------------------------
    b.chapter("bottom_cleaning", "BOTTOM CLEANING", [16])
    steps = [
        "Ensure all protective covers on the product are securely closed to prevent water ingress during rinsing.",
        "Lay a dry towel on the floor and place the product upside down on the towel as shown in the illustration to "
        "protect the surface.",
        "Follow the illustrated order to remove the screws at the bottom and take off the bottom panel to expose the "
        "internal cooling fins.",
        "Rinse the cooling fins with clean water. You may use a long-bristle brush or a damp cloth to help clean "
        "surface dirt. After cleaning, dry thoroughly with a towel and air dry in a shaded area. Ensure no moisture "
        "remains before reinstalling the bottom panel.",
    ]
    for number, step in enumerate(steps, start=1):
        b.add(OL(step, start=number))
        b.figure(f"cleaning-{number}")

    # ---- p17 STORAGE, TROUBLESHOOTING (printed 14) ---------------------------------------------
    b.chapter("storage", "STORAGE", [17])
    b.add(P("Store the product in a dry clean place with proper ventilation. Storage temperature and humidity:"),
          UL("1 month: -20°C to 45°C (0-60%RH)",
             "3 months: 0°C to 45°C (0-60%RH)",
             "12 months: 0°C to 25°C (0-60%RH)"),
          P("If this product is stored for a long period of time (3 months - 6 months) with the power depleted, it may "
            "become unchargeable. To prevent this and maintain battery health, it is recommended to check and recharge "
            "the product every three months and perform a full charge and discharge cycle at least once every 6 to 12 "
            "months."))
    b.chapter("troubleshooting", "TROUBLESHOOTING", [17])
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
            "If you charge the product via a solar panel, check the open-circuit voltage (Voc) of the connected solar "
            "panel. The product allows a maximum DC input voltage of 60V.",
            "Restart the product and keep it idle. Wait until the fault disappears.")},
        {**pair("F8", "code"), **pair("Contact Jackery Customer Support.", "measures")},
        {**pair("F9", "code"), **pair("Remove the load connected to the DC12V/USB ports of the product. Wait until the "
                                      "fault disappears.", "measures")},
    ]
    b.comp(troubleshooting_component_spec, headers=[pair("Error Code", "content"), pair("Corrective Measures", "content")],
           rows=rows)

    # ---- p18 SPECIFICATIONS (printed 15) --------------------------------------------------------
    b.chapter("specifications", "SPECIFICATIONS", [18])
    for title, rows in [
        ("GENERAL INFO", [("Product Name", "Jackery Explorer 1500 Ultra"), ("Model No.", "JE-1500C"),
                          ("Capacity", "30Ah/51.2V DC (1536Wh)"), ("Cell Chemistry", "LiFePO₄"),
                          ("Weight", "Around 38.6 lbs / 17.5 kg"), ("Dimension", "13.2×10.4×11.6 in / 33.6×26.4×29.5 cm"),
                          ("Cycle Life", "4000 cycles to 70%+ capacity"), ("IP Rating", "IP65 (All lids closed)")]),
        ("INPUT PORTS", [("Charge Mode AC Input", "100-120V ~ 60Hz, 15A Max"),
                         ("Bypass Mode AC Input", "100-120V ~ 60Hz, 12A Max"),
                         ("2 × DC8020 Ports", f"Car: 12-16V{DC}8A Max, Double to 8A Max"),
                         ("", f"PV: 16-60V{DC}12A, Double to 24A / 800W Max")]),
        ("OUTPUT PORTS", [("3 × AC Output", "120V ~ 60Hz, 1800W"),
                          ("AC Output in Bypass Mode¹", "100-120V ~ 60Hz, 12A Max"),
                          ("AC Total Output", "1800W Rated (2000W for 15min. Max) 3600W Surge Peak"),
                          ("1 × USB-A Output", f"18W Max, 5-6V{DC}3A, 6-9V{DC}2A, 9-12V{DC}1.5A"),
                          ("1 × USB-C1 Output", f"30W Max, 5V{DC}3A, 9V{DC}3A, 12V{DC}2.5A, 15V{DC}2A, 20V{DC}1.5A"),
                          ("1 × USB-C2 Output", f"100W Max, 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A"),
                          ("DC 12V Port", f"12V{DC}10A Max")]),
        ("ENVIRONMENTAL OPERATING TEMPERATURE", [("Charge Temperature", "32°F to 113°F / 0°C to 45°C"),
                                                 ("Discharge Temperature", "5°F to 113°F / -15°C to 45°C"),
                                                 ("", "5°F to 14°F / -15°C to -10°C  Output Power: 1000W")]),
    ]:
        b.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows)
    b.add(P("1 The product can charge the battery from the AC wall outlet while delivering power through the AC output "
            "ports."),
          P("※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."))

    # ---- p19 WARRANTY (printed 16) --------------------------------------------------------------
    b.chapter("warranty", "WARRANTY", [19])
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
        ("Repair or Replacement", blocks(
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
    ]
    for index, (title, body) in enumerate(sections, start=1):
        b.h(title)
        if body is None:
            b.comp(warranty_years_component_spec, title=title, periods=[
                {"number": "3", "unit": "YEARS", "label": "Standard Warranty",
                 **_body(
                     "The standard warranty period for Jackery Explorer 1500 Ultra is 36 months. In each case, the "
                     "warranty period is measured starting on the date of purchase by the original consumer purchaser. "
                     "The sales receipt from the first consumer purchase, or other reasonable documentary proof, is "
                     "required in order to establish the start date of the warranty period.")},
                {"number": "2", "unit": "YEARS", "label": "Extended Warranty",
                 **_body(
                     "To activate the Warranty Extension, you must register your product online  or contact our "
                     "customer service team at hello@jackery.com to extend the standard warranty runtime.")},
            ])
            continue
        b.comp(warranty_section_component_spec, title=title, section_index=index, blocks=body)

    # ---- p20-21 APP SETUP (printed 17-18) ---------------------------------------------------------
    b.chapter("app_setup", "APP SETUP", [20, 21])
    b.h("1. To download the App and log in")
    columns = [{"role": "store", "text": "Search for \"Jackery\" in Google Play or App Store to install the App. After "
                                         "that, you can register and log in."},
               {"role": "qr", "text": "Alternatively, scan the QR code below to download and install the App."}]
    for column in columns:
        column["html"] = escape(column["text"])
    b.used_figures += ["app-store", "app-qr"]
    store, qr = b.figures["app-store"]["local_path"], b.figures["app-qr"]["local_path"]
    b.comp(app_download_component_spec,
           lambda spec: [node("image", source=qr, alt="Jackery App"), *(P(c["text"]) for c in columns)],
           accessibility_label="Jackery App", columns=columns, source_art_ref=qr, store_art_ref=store, qr_art_ref=qr)
    b.h("2. To add device")
    before, after = "2.1 Click the button", "to add your device."
    b.comp(app_inline_control_component_spec,
           lambda spec: [node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])],
           accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
           paragraph_text=f"{before} + {after}", metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    b.add(P("2.2 Long press the “POWER” button on the device to turn on, the Wi-Fi and Bluetooth icons on the device "
            "flash to indicate that the device has entered the network configuring mode, tap the “Icon Flashed” button "
            "and allow the App to connect to nearby devices and open Bluetooth permissions."))
    b.figure("app-add")
    b.figure("app-control")
    b.callout("NOTE", "If the device is not connected to the App within 2 hours after being turned on, it will "
              "automatically turn off Wi-Fi and Bluetooth.", variant="note")
    b.add(P("2.3 After tapping the searched device icon, the App automatically connects the device via Bluetooth."))  # p21
    b.callout("NOTE", P("If \"the device has been bound\" is prompted during the binding process, the following two ways "
                        "can be used for connection:"),
              UL("The device owner will share this device with other users through the App.",
                 "Turn off the product, then press and hold the POWER button for 10 seconds to reset the device and "
                 "rebind it to the App."), variant="note")
    b.add(P("2.4 After the device is successfully connected, enter your Wi-Fi password and tap the OK button."))
    b.callout("NOTE", "Please select a Wi-Fi network in 2.4GHz band. The device does not support a Wi-Fi network in "
              "5GHz band.", variant="note")
    b.add(P("2.5 After the device is successfully added on the App, the Wi-Fi icon on the device will be always on."))
    b.figure("app-results")
    b.add(P("The above screenshots are for reference only."))
    b.h("3. To unbind the device")
    b.add(P("Click the Settings icon in the upper right corner of the main interface of the device to enter the settings "
            "page, and click the Unbind button at the bottom of the page to unbind the device."))
    b.h("4. Notes")
    b.h("4.1 To turn on Wi-Fi and Bluetooth:", level=4)
    b.add(UL("Wi-Fi and Bluetooth are automatically turned on after the device is on, and the Wi-Fi and Bluetooth "
             "icons on the screen light up."))
    b.h("4.2 To turn off Wi-Fi and Bluetooth:", level=4)
    b.add(UL("Wi-Fi and Bluetooth will be automatically turned off if no device is connected within 2 hours."))
    b.h("4.3 To reset Wi-Fi and Bluetooth:", level=4)
    b.add(UL("Turn off the product, then press and hold the POWER button for 10 seconds to reset Wi-Fi and Bluetooth "
             "to factory settings and reboot the system."))

    # ---- p22 back cover: contact -------------------------------------------------------------------
    b.chapter("contact", "JACKERY INC.", [22])
    b.add(P("5310 Bunche Dr., Fremont, CA 94538-8301"),
          P("1-888-502-2236 (US)\nhello@jackery.com\nwww.jackery.com"))
    b.figure("contact-qr")

    problems = b.finish()
    print("chapters", len(b.chapters), "problems", problems)
    return problems


def _body(value: str) -> dict:
    return {"body_html": "<p>" + escape(value) + "</p>", "body_text": value}


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
