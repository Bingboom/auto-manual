"""Write the JE-880B US English semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-880B/US/en/git-20261027-640e83ca/source/intake.py``.
It writes ``source/en/content.json``. ``original.pdf`` is outlined (no text
layer), so every English line below is transcribed from 300 dpi renders of the
named physical page and kept as printed, source slips included (listed in
``source_manifest.json:source_concerns``). Every printed block maps to a shared
component or plain shared flow (``source_manifest.json:component_map``); no
package class, inline style or plain table. The cover (p1) is not Web content.
"""
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import OL, P, Book, blocks, cell_pair, inbox_carrier, inline, spec_carrier  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.web.frozen_ai_flow import node, text  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
DC = "⎓"  # the print's DC symbol


def make() -> list[str]:
    b = Book(SOURCE, "JE-880B", "US", "en", "Jackery Explorer 880 Pro · JE-880B")
    glyphs = {g["slot"]: g for g in json.loads((SOURCE / "source/glyphs.json").read_text())}
    used_glyphs = []

    def glyph_lead(label: str, slot: str, alt: str, close: str, body: str) -> dict:
        """A bold run-in subheading that prints an LCD pictogram in parentheses."""
        used_glyphs.append(slot)
        return node("paragraph", [node("strong", [text(label + " (")]),
                                  node("image", source=glyphs[slot]["local_path"], alt=alt),
                                  node("strong", [text(close)]), node("line_break"), *inline(body)])

    # ---- p2-3 opening, TECHNICAL SPECIFICATIONS, certifications, FCC ---------------------
    b.chapter("introduction", "Model: JE-880B", [2, 3])
    b.add(P("Congratulations on your new Jackery Explorer 880 Pro. Please read this manual carefully before using "
            "the product, particularly the relevant precautions to ensure proper use. Keep this manual in an "
            "accessible place for frequent reference."),
          P("In compliance with laws and regulations, the right of final interpretation of this document and all "
            "related documents of this product resides with the Company."),
          P("Please note that no further notifications will be given in case of any update, revision or termination."))
    b.comp(spec_table_component_spec, spec_carrier, section_title="TECHNICAL SPECIFICATIONS", rows=[
        ("Product Name:", "Jackery Explorer 880 Pro"),
        ("Model No.:", "JE-880B"),
        ("Capacity:", "Lithium-ion 20.4Ah/43.2V DC(881Wh)"),
        ("Dimensions:", "34.0x26.2x25.5cm/13.39x10.32x10.06 in & About 11kg/ About 24.25 lbs"),
        ("Cycle Life:", "1000 cycles to 80%+ capacity"),
        ("3 x AC Output:", "120V~60Hz 8.34A Max, 1000W rated output, 2000W peak surge"),
        ("2 x USB-A output:", f"18W Max 5-6V{DC}3A, 6-9V{DC}2A, 9-12V{DC}1.5A"),
        ("2 x USB-C Output:", f"100W Max 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A"),
        ("Car Port:", f"12V{DC}10A"),
        ("Charge mode AC Input:", "100V-120V~ 60Hz, 15A Max"),
        ("Bypass mode AC Output:", "100V-120V~ 60Hz, 1000W Max"),
        ("DC Input:", f"17.5-60V{DC}11A, double to 11A/400W Max"),
        ("", f"12-17.5V{DC}8A, double to 8A Max"),
        ("Charge Temperature:", "0~40 °C (32~104 °F)"),
        ("Discharge Temperature:", "-10~40 °C (14~104 °F)"),
    ])
    b.add(P("**CERTIFICATIONS:**"))
    b.figure("certifications")
    b.add(P("※USB Type-C®and USB-C®are registered trademarks of USB Implementers Forum."),
          P("NOTE: This equipment has been tested and found to comply with the limits for a Class B digital device, "
            "pursuant to part 15 of the FCC Rules. These limits are designed to provide reasonable protection against "
            "harmful interference in a residential installation. This equipment generates, uses and can radiate radio "
            "frequency energy and, if not installed and used in accordance with the instructions, may cause harmful "
            "interference to radio communications. However, there is no guarantee that interference will not occur in "
            "a particular installation. If this equipment does cause harmful interference to radio or television "
            "reception, which can be determined by turning the equipment off and on, the user is encouraged to try to "
            "correct the interference by one or more of the following measures:\n"
            "--Reorient or relocate the receiving antenna.\n"
            "--Increase the separation between the equipment and receiver.\n"
            "--Connect the equipment into an outlet on a circuit different from that to which the receiver is "
            "connected.\n"
            "--Consult the dealer or an experienced radio/TV technician for help."),
          P("**MODIFICATION:** Any changes or modifications not expressly approved by the grantee of this device could "
            "void the user’s authority to operate the device."))                              # p3

    # ---- p3 PACKAGE LIST, GET TO KNOW YOUR GEAR ---------------------------------------------
    b.chapter("in_the_box", "PACKAGE LIST", [3])
    slots = ("inbox-unit", "inbox-car-cable", "inbox-ac-cable", "inbox-adaptor", "inbox-quick-start-guide")
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="PACKAGE LIST",
           cards=[{"image_ref": b.figures[s]["local_path"], "label": b.figures[s]["caption"],
                   "alt": b.figures[s]["caption"]} for s in slots],
           tip_label="", tip_body="", require_tip=False, variant="responsive-card-grid")
    b.chapter("product_overview", "GET TO KNOW YOUR GEAR", [3])
    b.h("Product Appearance")
    b.figure("product-appearance")

    # ---- p4-5 LCD Display ---------------------------------------------------------------------
    b.chapter("lcd_display", "LCD Display", [4, 5])
    b.figure("lcd-display")
    b.add(OL("Input Power", "Remaining Charge Time", "Solar Charging Indicator", "AC Wall Charging Indicator",
             "Car Charging Indicator", "Low Battery Indicator", "Remaining Battery Percentage", "Output Power",
             "Remaining Discharge Time", "Error Code", "High Temperature Warning", "Low Temperature Warning",
             "Low Power Mode", "AC Power Indicator", "Battery Power Indicator"))
    b.add(glyph_lead("Battery Power Indicator", "glyph-battery-power", "Battery Power Indicator", ") :",
                     "When the product is being charged, the orange circle around the battery percentage will light "
                     "up in sequence. When charging other devices, the orange circle will stay on."),
          glyph_lead("Low Battery Indicator", "glyph-low-battery", "Low Battery Indicator", ") :",
                     "When the battery is less than 20%, the Low Battery Indicator will stay on. When less than 5%, the "
                     "Low Battery Indicator will flash. When it is being charged, the Indicator will be off."),
          glyph_lead("Low Power Mode", "glyph-low-power-mode", "Low Power Mode", ") :",
                     "To avoid forgetting to turn off the output during use that results in battery consumption, the "
                     "product turns the Low Power Mode off by default. This occurs when no device is connected or the "
                     "connected device is less than or equal to a certain value. (Refer to the table below for more "
                     "details), the device will automatically shut down after 12 hours."))
    shutdown = "The device will automatically shut down after 12 hours"
    b.comp(reference_table_component_spec, variant="lcd-actions", label="Low Power Mode",
           headers=[cell_pair("Output"), cell_pair("Output Power"), cell_pair("Defaults")],
           rows=[[cell_pair(o), cell_pair(w), cell_pair(shutdown)]
                 for o, w in [("AC Output", "≤25W"), ("USB Output", "≤2W"), ("Car Output", "≤2W")]])
    b.add(P("**To turn on the Low Power Mode:** Long press the AC Button and DISPLAY Button until the Low Power Mode "
            "icon lights up. In Low Power Mode, please remember to turn off the output to avoid battery consumption.\n"
            "**To turn off the Low Power Mode:** Long press the AC Button and DISPLAY Button until the Low Power Mode "
            "icon disappears on the screen."),
          glyph_lead("Fault code", "glyph-fault-code", "Fault code", ") :",
                     "In order to quickly solve the user’s feedback, we set up common fault codes F0-F9 in the system: "
                     "if you find any fault code of F0、F1、F2、F3、F4、F7 on the display screen, please contact us for "
                     "after-sales treatment; If F6 code appears, please remove the load or unplug the charging plug, "
                     "the product can restore by itself, if not, please contact after-sales treatment; If F9 fault code "
                     "appears, please remove the load and the product can recover by itself, if not, please contact "
                     "after-sales service."),
          glyph_lead("High-temperature warning", "glyph-high-temperature", "High-temperature warning", ") :",  # p5
                     "If it appears on the screen, do not worry, the battery will restore automatically after cooling."),
          glyph_lead("Low-temperature Warning", "glyph-low-temperature", "Low-temperature Warning", ") :",
                     "If it is displayed on the screen, do not worry. It will automatically restore after the ambient "
                     "temperature is restored."))

    # ---- p5 Basic Operations ------------------------------------------------------------------
    b.chapter("operations", "Basic Operations", [5])
    b.h("Power On/Off")
    b.add(P("**AC Output On/Off:** Press the AC Button, the AC Output operation indicator lights up. Then you can "
            "connect the equipment that needs AC charging. Press the AC Button again to turn off the AC Output.\n"
            "**USB Output On/Off:** Press the USB Button, the USB Output operation indicator lights up. Then USB-A and "
            "USB-C Output Ports can be connected to external load devices. Press the USB Button again to turn off the "
            "USB Output.\n"
            "**Car Port On/Off:** Press the Car Port Button, the Car Port operation indicator lights up. Then the Car "
            "Port can be connected to the external load devices. Press the Car Port Button again to turn off the output."))
    b.h("LCD Screen On/Off")
    b.add(P("To Turn On, press the DISPLAY Button, any Output Power Button, or LED Light Button. Or, when there’s a "
            "charging input, the screen display will light up automatically.\n"
            "To Turn Off, press the DISPLAY Button again and the screen display will turn off. Or, if there is no "
            "operation in 30 seconds, the product will enter a sleep state and the screen display will automatically "
            "turn off.\n"
            "**To get the screen always-on (under charging or discharging state), follow these steps:** After the "
            "display screen lights up, double-click the DISPLAY Button and the mode of Always-On Display will be on.\n"
            "**To turn off Always-On Display, follow these steps:** Press the DISPLAY Button and the screen will be "
            "turned off in 30 seconds.\n"
            "**Tip:**During Always-On mode, the screen automatically turns off after 2 hours without charging or "
            "discharging."))
    b.h("LED Light On/Off")
    b.add(P("**There are three modes of LED Light:** Low Light mode, Bright Light mode, and SOS mode.\n"
            "**The operations are as follows:** Press the LED Light Button, the LED will be turned on. The light will "
            "always turn on in Low Light mode and the output power on the screen is 1W. Press again to enter the "
            "Bright Light mode and the output power on the screen is 3W. Press the third time to enter the SOS mode and "
            "the output power on the screen is 3W. Then, press again to turn off the LED Light. In any of these modes, "
            "the light can be turned off by a long press."))

    # ---- p5-7 CHARGING ------------------------------------------------------------------------
    b.chapter("charging", "CHARGING YOUR JACKERY EXPLORER 880 PRO", [5, 6, 7])
    b.add(P("**Green energy first:** We advocate to use the green energy first. This product supports two modes of "
            "charging at the same time: solar charging and AC wall charging.\n"
            "When AC wall charging and solar charging are turned on at the same time, the product will give priority "
            "to solar charging and both methods will be used to charge the battery at the maximum permissible power."))
    b.h("Charging from the wall")                                                         # p6
    b.add(P("Please use the AC cable included in the package."))
    b.figure("charging-wall")
    b.h("Solar energy charging")
    b.h("Jackery SolarSaga 200 or 100 or 80 Solar Panel Connection Guide", level=4)
    b.add(P("If one or two solar panels are connected, you can directly connect the DC8020 port of the solar panel to "
            "the DC8020 port of Jackery Explorer 880 Pro for charging. If four solar panels are connected, please refer "
            "to the method shown in the following figure to charge through the solar series connector (Note: The solar "
            "series connector is not in standard configuration, so you need to purchase it separately. Please refer to "
            "the detailed operation instructions of the solar series connector before using it.)"))
    b.figure("solar-two-panels")
    b.figure("solar-four-panels")
    b.add(P("**Tip:** Jackery Explorer 880 Pro does not support three Jackery SolarSaga 200 or 100 or 80 solar panels "
            "in single input; otherwise, over-voltage protection will be triggered."))
    b.h("Jackery SolarSaga 80 Solar Panel Connection Guide", level=4)
    b.add(P("Users who have purchased Jackery SolarSaga 80 can charge the product by referring to the connection mode "
            "shown below. The Jackery SolarSaga 80 supports the parallel connection or the parallel and then series "
            "connections to charge the product. The single input port of the Jackery Explorer 880 Pro supports the "
            "input of up to six pieces of SolarSaga 80 solar panels, and two input ports support the input to up to 6 "
            "pieces of SolarSaga 80 solar panels. (When the power is connected with six solar panels in a single input "
            "port, the solar panels shall be divided into two groups, and each group of three solar panels shall be "
            "self-connected in parallel and then connected to Jackery Explorer 880 Pro through the solar series "
            "connector. The solar series connector needs to be purchased separately.)\n"
            "For detailed operation instructions on the self-parallel connection of the Jackery SolarSaga 80 solar "
            "panel, please refer to the user manual."))
    b.figure("solarsaga80-parallel")                                                       # p7
    b.add(P("**Warm Tip:** Users can enter the number of solar panels in their own combination according to the number "
            "of solar panels they purchased. Currently, the product supports charging with 1, 2, 3, 4, 5, 6, 8, and 12 "
            "80W solar panels in combination."))
    b.h("DC7909 to DC8020 Adaptor Operation Guide", level=4)
    b.add(P("All of our solar panels on sale have been upgraded to include a DC7909 to DC8020 adapter. If you have "
            "purchased a Jackery solar panel without a DC7909 to DC8020 adapter, you can charge your Jackery Explorer "
            "880 Pro by following the connection instructions below."))
    b.figure("dc7909-adaptor")
    b.h("Charging in the Car")
    b.add(P("This product can be charged with a 12V car charger. Please start the vehicle before charging to prevent "
            "draining the car battery and prevent your vehicle from being unable to start.\n"
            "Meanwhile, please ensure that the car charger and the car cigarette lighter provide a good connection, and "
            "ensure that the car charger is fully inserted. In addition, if the vehicle is running on bumpy roads, it is "
            "forbidden to use the car charger in case it burns due to a poor connection. The Company will not be "
            "responsible for any loss caused by non-standard operation."))
    b.figure("charging-car")
    b.h("Safety Precautions When Charging")
    b.add(P("1) Vehicle charging is only applicable in 12V vehicles, not in 24V ones. Please do not charge this product "
            "in 24V vehicle to avoid personal injury and property loss.\n"
            "2) It is recommended to use Jackery accessories - solar panels for solar charging. We will not be "
            "responsible for the losses caused by using other brands’ solar panels."))

    # ---- p7-8 SAFETY PRECAUTIONS WHEN USING ---------------------------------------------------
    b.chapter("safety_using", "SAFETY PRECAUTIONS WHEN USING", [7, 8])
    b.add(P("**The basic safety precautions should be followed when using this product, including:**\n"
            "a. Please read all instructions before using this product.\n"
            "b. Close supervision is required when using this product near children to reduce the risk.\n"
            "c. Risk of electric shock may occur if using accessories recommended or sold by non-professional product "
            "manufacturers.\n"
            "d. When the product is not in use, please unplug the power plug from the product's socket.\n"
            "e. Do not dismantle the product, which may lead to unpredictable risks such as fire, explosion or electric "
            "shock.\n"
            "f. Do not use the product through damaged cords or plugs, or damaged output cables, which may cause "
            "electric shock.\n"
            "g. Charge the product in a well ventilated area and do not restrict ventilation in any way.\n"
            "h. Please put the product in a ventilated and dry place to avoid rain and water to cause electric shock.\n"
            "i. Do not expose the product to fire or high temperature (under direct sunlight or in vehicle under high "
            "heat), which may cause accidents such as fire and explosion.\n"
            "j.Do not disassemble the power pack, take it to a qualified service person when service or repair is "
            "required. Incorrect reassembly may result in a risk of fire or electric shock.\n"
            "k.Have servicing performed by a qualified repair person using only identical replacement parts. This will "
            "ensure that the safety of the product is maintained."))

    # ---- p8-9 INSTRUCTIONS PERTAINING TO RISK OF FIRE ... -------------------------------------
    b.chapter("safety", "INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS", [8, 9])
    b.h("Important Safety Instructions")
    b.add(P("WARNING–When using this product, basic precautions should always be followed, including the following:\n"
            "a) Read all the instructions before using the product.\n"
            "b) To reduce the risk of injury, close supervision is necessary when the product is used near children.\n"
            "c) Do not put fingers or hands into the product.\n"
            "d) Use of an attachment not recommended or sold by power pack manufacturer may result in a risk of fire, "
            "electric shock, or injury to persons.\n"
            "e) To reduce risk of damage to the electric plug and cord, pull the plug rather than the cord when "
            "disconnecting the power pack.\n"
            "f) Do not use a battery pack or appliance that is damaged or modified. Damaged or modified batteries may "
            "exhibit unpredictable behavior resulting in fire, explosion or risk of injury.\n"
            "g) Do not operate the power pack with a damaged cord or plug, or a damaged output cable.\n"
            "h) Do not disassemble the power pack, take it to a qualified service person when service or repair is "
            "required. Incorrect reassembly may result in a risk of fire or electric shock.\n"
            "i) To reduce the risk of electric shock, unplug the power pack form the outlet before attempting any "
            "instructed servicing.\n"
            "j) PERSONAL PRECAUTIONS\n"
            "1)Have plenty of fresh water and soap nearby in case battery acid contacts skin, clothing, or eyes.\n"
            "2)Wear complete eye protection and clothing protection. Avoid touching eyes while working near battery.\n"
            "3)If battery acid contacts skin or clothing, wash immediately with soap and water. If acid enters eye, "
            "immediately flood eye with running cold water for at least 10 minutes and get medical attention "
            "immediately.\n"
            "4)NEVER smoke or allow a spark or flame in vicinity of battery or engine.\n"
            "5)Be extra cautious to reduce risk of dropping a metal tool onto battery. It might spark or short-circuit "
            "battery or other electrical part that may cause explosion.\n"
            "k) When charging the internal battery, work in a well ventilated area and do not restrict ventilation in "
            "any way.\n"
            "l) Under abusive conditions, liquid may be ejected from the battery; avoid contact. If contact accidentally "
            "occurs, flush with water. If liquid contacts eyes, additionally seek medical help. Liquid ejected from the "
            "battery may cause irritation or burns.\n"
            "m) Do not expose a power pack to fire or excessive temperature. Exposure to fire or temperature above 130°C "
            "may cause explosion. The temperature of 130°C can be replaced by the temperature of 265°F.\n"
            "n) Have servicing performed by a qualified repair person using only identical replacement parts. This will "
            "ensure that the safety of the product is maintained."))
    b.h("Operating Instructions")                                                          # p9
    b.add(P("Use and store the unit only in a clean and dry environment. DO NOT use and store in dusty and wet "
            "environment.\n"
            "Check the unit prior to every use. DO NOT use the unit if it is damaged, broken.\n"
            "If rust, peculiar odors, overheating or other abnormal circumstances are observed, stop using the unit "
            "immediately and contact the dealer or our customer service center.\n"
            "Make sure that the unit is properly secured when transporting it in a motor vehicle.\n"
            "Only charge, use and store the unit within an ambient temperature\n"
            "Switch the unit off immediately if it has accidentally fallen, was dropped or was exposed to vibrations.\n"
            "DO NOT use the unit if the power cord is damaged or broken.\n"
            "Keep the unit away from children. DO NOT let children use the power supply unit. Keep this product away "
            "from pets.\n"
            "DO NOT use the unit in an area or environment with high temperature.\n"
            "Should fluid from inside of the unit come in contact with your skin or clothing, wash the affected areas "
            "with tap water.\n"
            "In a storm, unplug the power cord from the socket.\n"
            "DO NOT charge the unit via power supply systems that operate outside of input rating.\n"
            "DO NOT place the unit on its side or upside down while in use or storage.\n"
            "DO NOT use accessories for other usage.\n"
            "Make sure that the device you are connecting is switched off before you connect it.\n"
            "DO NOT expose a power pack to fire or excessive temperature. Exposure to fire or temperature above 130°C "
            "may cause explosion.\n"
            "Solar charge times depend on weather conditions, place your solar panel where it will get as much direct "
            "sunlight as possible.\n"
            "DO NOT place the power pack on the floor, or at a height less than 457 mm (18 inches) above the floor, "
            "during use in a repair facility.\n"
            "Warning： Do not remove the battery pack without permission,If you need to repair the battery pack, "
            "contact your local manufacturer as soon as possible\n"
            "DANGER: This device is intended to be used indoors only. Do not use outdoors under any conditions."))
    b.h("Charging instruction")
    b.add(P("1.The product supports any 1 way or 2 way charging .\n"
            "2.Charge the Portable Power Station with charger; the LCD will turn on and display Input power\n"
            "3.Display will show 100% capacity when fully charged ."))
    b.h("Discharging instruction")
    b.add(P("1.Press the AC button, AC output will be turn on; and press the button again, the AC output will turn off， "
            "while the AC LED will turn off within 1~2seconds.\n"
            "2.Press the any 1or 2 way DC(USB or 12V) button, output will be turn on; and press the button again, the "
            "DC output will turn off， while the DC LED will turn off within 1~2seconds.\n"
            "3. If DC or AC output is on LCD will display “OUPUT” icon and output power unless all DC output is off"))

    # ---- p10 MOVING AND STORAGE, USER MAINTENANCE, WARRANTY -----------------------------------
    b.chapter("storage", "MOVING AND STORAGE INSTRUCTIONS", [10])
    b.add(P("DO NOT move the unit if it is recharging or in use.\n"
            "DO NOT dispose the unit together with household waste.\n"
            "DO NOT place the unit close to or in a fire or expose it to heat. Keep out of direct sunlight.\n"
            "DO NOT store the unit in a bathroom or in an area exposed to rain or moisture.\n"
            "DO NOT disassemble the power pack, take it to a qualified service person when service or repair is "
            "required. Incorrect reassembly may result in a risk of fire or electric shock.\n"
            "DO NOT store the unit in an area or environment with high temperature."))
    b.chapter("maintenance", "USER MAINTENANCE INSTRUCTIONS", [10])
    b.add(P("Before using or storing, plug your Jackery Explorer into the wall until it is fully charged. If you see the "
            "LCD battery is low at any point, plug it into a power source, like an AC outlet or a solar panel as soon as "
            "possible.\n"
            "To preserve the battery lifespan, please use and recharge at least once every 6 months.\""))
    b.chapter("warranty", "WARRANTY", [10])
    b.add(P("**Note: We only provide our warranty for the buyer who purchased on Amazon (Jackery Inc.), Jackery website "
            "or local authorized dealers.**"))
    sections = [
        ("Limited Warranty", blocks(
            "Jackery Inc. warrants to the original consumer purchaser that the Jackery product will be free from defects "
            "in workmanship and material under normal consumer use during the applicable warranty period identified in "
            "the 'Warranty Period' section below, subject to the exclusions set forth below.",
            "This warranty statement sets forth Jackery's total and exclusive warranty obligation. We will not assume, "
            "nor authorize any person to assume for us, any other liability in connection with the sale of our "
            "products.")),
        ("Warranty Period", blocks(
            "3 Years Standard Warranty: The standard warranty period for Jackery Explorer 880 Pro is 36 months. In each "
            "case, the warranty period is measured starting on the date of purchase by the original consumer purchaser. "
            "The sales receipt from the first consumer purchase, or other reasonable documentary proof, is required in "
            "order to establish the start date of the warranty period.",
            "2 Years Extended Warranty: To activate the Warranty Extension, you must register your product online or "
            "contact our customer service team at hello@jackery.com to extend the standard warranty runtime.")),
        ("Exchange", blocks(
            "Jackery will replace (at Jackery's expense) any Jackery product that fails to operate during the "
            "applicable warranty period due to defect in workmanship or material. A replacement product assumes the "
            "remaining warranty of the original product.")),
        ("Limited to Original Consumer Buyer", blocks(
            "The warranty on Jackery's product is limited to the original consumer purchaser and is not transferable "
            "to any subsequent owner.")),
        ("Exclusions", blocks(
            "Jackery's warranty does not apply to:",
            "Misused, abused, modified, damaged by accident, or used for anything other than normal consumer use as "
            "authorized in Jackery's current product literature.",
            "Attempted repair by anyone other than an authorized facility.",
            "Any product purchased through an online auction house.",
            "Jackery's warranty does not apply to the battery cell unless the battery cell is fully charged by you within "
            "seven days after you purchase the product and at least once every 6 months thereafter.")),
    ]
    for index, (title, body) in enumerate(sections, start=1):
        b.h(title)
        b.comp(warranty_section_component_spec, title=title, section_index=index, blocks=body)

    # ---- p11 back cover: contact ----------------------------------------------------------------
    b.chapter("contact", "JACKERY INC.", [11])
    b.add(P("5310 Bunche Dr, Fremont, CA 94538\n"
            "Tel:1-888-502-2236(US) E-mail:hello@jackery.com Website:www.jackery.com"))
    b.figure("contact-qr")

    problems = b.finish()
    problems += [f"unused glyph {s}" for s in sorted(set(glyphs) - set(used_glyphs))]
    print("chapters", len(b.chapters), "problems", problems)
    return problems


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
