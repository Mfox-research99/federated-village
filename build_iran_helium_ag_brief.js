const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat,
  TabStopType, TabStopPosition
} = require('docx');
const fs = require('fs');

const NAVY="1B3A5C", GOLD="B8860B", LGOLD="F5F0E0", LNAVY="E8EEF4",
      LGREEN="EAF4EA", DGREEN="2E6B2E", LRED="FDF0F0", DRED="8B0000",
      WHITE="FFFFFF", BLACK="1A1A1A", MGREY="555555", LGREY="F5F5F5";

const b1=(c)=>({style:BorderStyle.SINGLE,size:6,color:c});
const nb={style:BorderStyle.NONE,size:0,color:"FFFFFF"};
const noBorders={top:nb,bottom:nb,left:nb,right:nb};
const cb=(c)=>({top:b1(c),bottom:b1(c),left:b1(c),right:b1(c)});
const sp=(b=100)=>new Paragraph({spacing:{before:b,after:0},children:[new TextRun("")]});
const body=(t,o={})=>new Paragraph({spacing:{before:60,after:80},children:[new TextRun({text:t,color:o.color||BLACK,size:22,font:"Arial",bold:o.bold||false,italics:o.italic||false})]});
const h1=(t)=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:300,after:80},border:{bottom:{style:BorderStyle.SINGLE,size:4,color:GOLD}},children:[new TextRun({text:t,color:NAVY,bold:true,size:28,font:"Arial"})]});
const h2=(t)=>new Paragraph({spacing:{before:180,after:60},children:[new TextRun({text:t,color:NAVY,bold:true,size:24,font:"Arial"})]});
const bullet=(t,sub=false)=>new Paragraph({numbering:{reference:"bullets",level:sub?1:0},spacing:{before:40,after:40},children:[new TextRun({text:t,color:BLACK,size:22,font:"Arial"})]});

const callout=(title,body_t,fill=LGOLD,border=GOLD,titleColor=NAVY)=>new Table({
  width:{size:9720,type:WidthType.DXA},columnWidths:[9720],
  rows:[new TableRow({children:[new TableCell({
    borders:{top:nb,bottom:nb,right:nb,left:b1(border)},
    shading:{fill,type:ShadingType.CLEAR},
    margins:{top:120,bottom:120,left:240,right:240},
    width:{size:9720,type:WidthType.DXA},
    children:[
      new Paragraph({children:[new TextRun({text:title,color:titleColor,bold:true,size:22,font:"Arial"})]}),
      new Paragraph({spacing:{before:60},children:[new TextRun({text:body_t,color:BLACK,size:21,font:"Arial"})]})
    ]
  })]})],
});

const alarmBox=(title,body_t)=>new Table({
  width:{size:9720,type:WidthType.DXA},columnWidths:[9720],
  rows:[new TableRow({children:[new TableCell({
    borders:cb(DRED),
    shading:{fill:LRED,type:ShadingType.CLEAR},
    margins:{top:160,bottom:160,left:320,right:320},
    width:{size:9720,type:WidthType.DXA},
    children:[
      new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:title,color:DRED,bold:true,size:24,font:"Arial"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[new TextRun({text:body_t,color:BLACK,size:21,font:"Arial"})]})
    ]
  })]})],
});

const dataRow=(cells,widths,shaded=false)=>new TableRow({children:cells.map((t,i)=>new TableCell({
  borders:cb("CCCCCC"),shading:{fill:shaded?LGREY:WHITE,type:ShadingType.CLEAR},
  margins:{top:70,bottom:70,left:100,right:100},
  width:{size:widths[i],type:WidthType.DXA},
  children:[new Paragraph({children:[new TextRun({text:t,color:BLACK,size:20,font:"Arial"})]})]
}))});

const hdrRow=(cells,widths)=>new TableRow({children:cells.map((t,i)=>new TableCell({
  borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},
  margins:{top:70,bottom:70,left:100,right:100},
  width:{size:widths[i],type:WidthType.DXA},
  children:[new Paragraph({children:[new TextRun({text:t,color:WHITE,bold:true,size:20,font:"Arial"})]})]
}))});

const actionBlock=(num,title,tier,body_t)=>new Table({
  width:{size:9720,type:WidthType.DXA},columnWidths:[9720],
  rows:[
    new TableRow({children:[new TableCell({borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},margins:{top:60,bottom:60,left:160,right:160},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:`${num}. ${title.toUpperCase()}`,color:WHITE,bold:true,size:20,font:"Arial"}),new TextRun({text:`   [${tier}]`,color:GOLD,size:18,font:"Arial"})]})]})]}),
    new TableRow({children:[new TableCell({borders:cb(NAVY),shading:{fill:LNAVY,type:ShadingType.CLEAR},margins:{top:100,bottom:100,left:200,right:200},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:body_t,color:BLACK,size:21,font:"Arial"})]})]})]})
  ],
});

const doc = new Document({
  numbering:{config:[{
    reference:"bullets",
    levels:[
      {level:0,format:LevelFormat.BULLET,text:"\u2022",alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:720,hanging:360}}}},
      {level:1,format:LevelFormat.BULLET,text:"\u25e6",alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:1080,hanging:360}}}}
    ]
  }]},
  styles:{
    default:{document:{run:{font:"Arial",size:22,color:BLACK}}},
    paragraphStyles:[{id:"Heading1",name:"Heading 1",basedOn:"Normal",next:"Normal",quickFormat:true,run:{size:28,bold:true,font:"Arial",color:NAVY},paragraph:{spacing:{before:300,after:80},outlineLevel:0}}]
  },
  sections:[{
    properties:{page:{size:{width:12240,height:15840},margin:{top:1080,right:1260,bottom:1080,left:1260}}},
    headers:{default:new Header({children:[new Paragraph({
      tabStops:[{type:TabStopType.RIGHT,position:TabStopPosition.MAX}],
      border:{bottom:{style:BorderStyle.SINGLE,size:6,color:GOLD}},
      spacing:{before:0,after:80},
      children:[
        new TextRun({text:"DOLLAR STABILITY IN A WORLD AT WAR  |  LEGISLATIVE BRIEF",color:NAVY,size:16,font:"Arial"}),
        new TextRun({text:"\t"}),
        new TextRun({text:"Page ",color:MGREY,size:16,font:"Arial"}),
        new TextRun({children:[PageNumber.CURRENT],color:MGREY,size:16,font:"Arial"}),
        new TextRun({text:" of ",color:MGREY,size:16,font:"Arial"}),
        new TextRun({children:[PageNumber.TOTAL_PAGES],color:MGREY,size:16,font:"Arial"}),
      ]
    })]}),},
    footers:{default:new Footer({children:[
      new Paragraph({border:{top:{style:BorderStyle.SINGLE,size:4,color:NAVY}},children:[]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[new TextRun({text:"Dollar Stability in a World at War  \u2022  Legislative Brief  \u2022  April 5, 2026",color:MGREY,size:16,font:"Arial",italics:true})]})
    ]})},
    children:[

// ── TITLE ───────────────────────────────────────────────────────────────────
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({
  borders:noBorders,shading:{fill:NAVY,type:ShadingType.CLEAR},
  margins:{top:320,bottom:320,left:480,right:480},
  width:{size:9720,type:WidthType.DXA},
  children:[
    new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"DOLLAR STABILITY IN A WORLD AT WAR",color:GOLD,bold:true,size:22,font:"Arial"})]}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[new TextRun({text:"Helium, Fertilizer, and the Cost of Doing Nothing",color:WHITE,bold:true,size:36,font:"Arial"})]}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:60},children:[new TextRun({text:"A Legislative Brief for the United States Congress",color:WHITE,size:22,font:"Arial"})]}),
    new Paragraph({alignment:AlignmentType.CENTER,border:{top:{style:BorderStyle.SINGLE,size:4,color:GOLD}},spacing:{before:80},children:[new TextRun({text:"April 5, 2026",color:GOLD,size:18,font:"Arial",italics:true})]})
  ]
})]})]}),
sp(160),

// ── STAFFER BRIEF ────────────────────────────────────────────────────────────
new Paragraph({children:[new PageBreak()]}),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({
  borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},
  margins:{top:200,bottom:200,left:360,right:360},
  width:{size:9720,type:WidthType.DXA},
  children:[
    new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"SUMMARY FOR THE SENATOR\u2019S OFFICE",color:GOLD,bold:true,size:24,font:"Arial"})]}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:60},children:[new TextRun({text:"Read this page. The rest of the document is the evidence behind it.",color:WHITE,size:20,font:"Arial",italics:true})]})
  ]
})]})]}),
sp(0),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({
  borders:{top:nb,bottom:b1(NAVY),left:b1(NAVY),right:b1(NAVY)},
  shading:{fill:LNAVY,type:ShadingType.CLEAR},
  margins:{top:160,bottom:160,left:360,right:360},
  width:{size:9720,type:WidthType.DXA},
  children:[
    new Paragraph({children:[new TextRun({text:"WHAT THIS PROPOSAL IS",color:NAVY,bold:true,size:22,font:"Arial"})]}),
    new Paragraph({spacing:{before:60,after:120},children:[new TextRun({text:"Replace the entire federal tax system \u2014 income, payroll, capital gains, excise \u2014 with a single flat rate on every cleared financial transaction. Same rate for everyone: 0.25\u20130.7%, deducted automatically at the clearing layer. No returns, no audits, no criminal liability. Revenue funds universal healthcare, a guaranteed income floor, and pays down the national debt. Constitutional under Article I, Section 8. No amendment required.",color:BLACK,size:21,font:"Arial"})]})
  ]
})]})]}),
sp(0),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[4860,4860],rows:[
  new TableRow({children:[
    new TableCell({borders:{top:nb,bottom:b1(NAVY),left:b1(NAVY),right:b1("CCCCCC")},shading:{fill:LGOLD,type:ShadingType.CLEAR},margins:{top:140,bottom:140,left:280,right:280},width:{size:4860,type:WidthType.DXA},children:[
      new Paragraph({children:[new TextRun({text:"WHY IT MATTERS TO THIS STATE\u2019S CONSTITUENTS",color:NAVY,bold:true,size:21,font:"Arial"})]}),
      new Paragraph({spacing:{before:60,after:40},children:[new TextRun({text:"Fertilizer:",color:BLACK,bold:true,size:20,font:"Arial"}),new TextRun({text:" The Strait of Hormuz closure is driving LNG prices up \u2192 ammonia up \u2192 fertilizer up. A 500-acre corn operation is looking at $40,000+ in extra input costs this planting season. Not a forecast. This spring.",color:BLACK,size:20,font:"Arial"})]})  ,
      new Paragraph({spacing:{before:40,after:40},children:[new TextRun({text:"Helium:",color:BLACK,bold:true,size:20,font:"Arial"}),new TextRun({text:" Every MRI machine in every rural hospital runs on helium. The Federal Helium Reserve was sold off. Qatar shares the world\u2019s largest gas field with Iran. Supply is constrained now.",color:BLACK,size:20,font:"Arial"})]})  ,
      new Paragraph({spacing:{before:40,after:40},children:[new TextRun({text:"Dollar reserve status:",color:BLACK,bold:true,size:20,font:"Arial"}),new TextRun({text:" US allies are building yuan/euro settlement infrastructure because dollar-denominated trade now carries confiscation risk. Once that infrastructure reaches critical mass \u2014 2027 \u2014 it is permanent.",color:BLACK,size:20,font:"Arial"})]})  ,
      new Paragraph({spacing:{before:40,after:0},children:[new TextRun({text:"Small businesses:",color:BLACK,bold:true,size:20,font:"Arial"}),new TextRun({text:" A 5-employee business currently pays $74,925/year in combined taxes and compliance. Under this proposal: $2,450. A 97% reduction. Healthcare overhead: gone.",color:BLACK,size:20,font:"Arial"})]})
    ]}),
    new TableCell({borders:{top:nb,bottom:b1(NAVY),left:b1("CCCCCC"),right:b1(NAVY)},shading:{fill:LGREEN,type:ShadingType.CLEAR},margins:{top:140,bottom:140,left:280,right:280},width:{size:4860,type:WidthType.DXA},children:[
      new Paragraph({children:[new TextRun({text:"WHAT THE SENATOR IS BEING ASKED TO DO",color:DGREEN,bold:true,size:21,font:"Arial"})]}),
      new Paragraph({spacing:{before:60,after:40},children:[new TextRun({text:"Immediate (no legislation required):",color:BLACK,bold:true,size:20,font:"Arial"}),new TextRun({text:" Call for a Treasury velocity study directive, Fed velocity reporting, and a public de-dollarization dashboard. These establish the data record before the legislative fight begins.",color:BLACK,size:20,font:"Arial"})]})  ,
      new Paragraph({spacing:{before:40,after:40},children:[new TextRun({text:"30-day legislation:",color:BLACK,bold:true,size:20,font:"Arial"}),new TextRun({text:" Introduce or co-sponsor a narrow Velocity Tax Pilot Act \u2014 0.1% on equity trades above $100,000 only. Bipartisan framing: flat tax, no audits, level playing field, productive economy wins.",color:BLACK,size:20,font:"Arial"})]})  ,
      new Paragraph({spacing:{before:40,after:40},children:[new TextRun({text:"30-day companion:",color:BLACK,bold:true,size:20,font:"Arial"}),new TextRun({text:" Dollar Reserve Protection Board to prevent weaponization of financial infrastructure against helium, ammonia, and other essential goods that allies are already routing around SWIFT to purchase.",color:BLACK,size:20,font:"Arial"})]})  ,
      new Paragraph({spacing:{before:40,after:0},children:[new TextRun({text:"The window:",color:DRED,bold:true,size:20,font:"Arial"}),new TextRun({text:" Settlement rail lock-in is estimated Q1\u2013Q4 2027. After that, structural reform can reduce harm but cannot restore what is lost. This is the Congress that decides.",color:BLACK,size:20,font:"Arial"})]})
    ]})
  ]})
]}),
sp(80),
callout(
  "THE 30-SECOND VERSION",
  "The Iran conflict is breaking three American supply chains: fertilizer, helium, and the dollar\u2019s reserve status. All three trace to the same structural failure: a tax system built for 1950 that ignores where the modern economy actually lives. A single flat rate on cleared financial transactions fixes the structural problem, eliminates taxes on productive businesses, and funds healthcare and pensions as infrastructure for a productive economy. The window to act before the damage becomes permanent is 18\u201324 months.",
  LGOLD, GOLD
),
sp(200),

// ── LEAD — THE PROBLEM TODAY ─────────────────────────────────────────────────
new Paragraph({children:[new PageBreak()]}),
h1("I. What Is Happening Right Now"),
body("The Strait of Hormuz is closed. Forty percent of the world\u2019s seaborne oil and liquefied natural gas moves through that strait. It is not moving now. The downstream effects are already hitting American farms, hospitals, and manufacturing plants \u2014 not as projections, but as current operating realities."),
sp(80),

alarmBox(
  "THREE AMERICAN SUPPLY CHAINS BREAKING TODAY",
  "Natural gas prices rising \u2192 ammonia production costs rising \u2192 fertilizer prices rising \u2192 farm input costs rising \u2192 food prices rising. This chain operates in real time. It does not wait for a diplomatic resolution."
),
sp(120),

h2("The Fertilizer Chain"),
body("Ammonia is the feedstock for virtually every nitrogen fertilizer used in American agriculture. The Haber-Bosch process \u2014 which converts atmospheric nitrogen into ammonia \u2014 runs on natural gas. It is energy-intensive by design. When LNG prices spike, ammonia production costs spike. When ammonia production costs spike, the price of urea, anhydrous ammonia, and UAN (urea-ammonium nitrate) \u2014 the three nitrogen fertilizers that corn, wheat, soybeans, and cotton cannot grow without \u2014 spike with them."),
sp(60),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[3600,3060,3060],rows:[
  hdrRow(["Crop","Nitrogen Fertilizer Dependence","Typical Cost Per Acre"],[3600,3060,3060]),
  dataRow(["Corn","150\u2013200 lbs nitrogen/acre","$90\u2013150 at normal prices"],[3600,3060,3060],false),
  dataRow(["Winter wheat","60\u2013120 lbs nitrogen/acre","$40\u201380 at normal prices"],[3600,3060,3060],true),
  dataRow(["Soybeans","Lower (nitrogen-fixing) but needs phosphate","$30\u201360 at normal prices"],[3600,3060,3060],false),
  dataRow(["Cotton","60\u201390 lbs nitrogen/acre","$40\u201370 at normal prices"],[3600,3060,3060],true),
]}),
sp(80),
callout(
  "THE STRAIT OF HORMUZ EFFECT ON AN IOWA CORN FARMER",
  "Anhydrous ammonia is the most common nitrogen fertilizer in the corn belt. In the 2021\u20132022 energy spike, anhydrous ammonia prices went from roughly $500/ton to over $1,500/ton \u2014 a 3x increase in one input alone. A 500-acre corn operation applying 175 lbs/acre needs approximately 40 tons of anhydrous. At $500/ton: $20,000. At $1,500/ton: $60,000. A $40,000 swing on a single input for a mid-size operation. The Strait of Hormuz closure is producing a comparable energy shock. It is not hypothetical. It is this planting season.",
  LGOLD, GOLD
),
sp(160),

h2("The Helium Chain"),
body("Helium is not a party supply problem. It is a critical industrial gas with no substitute in three essential applications: MRI machines, semiconductor fabrication, and fiber optic cable production. The United States sold off the Federal Helium Reserve \u2014 built in Amarillo, Texas \u2014 through a congressionally mandated sale process that concluded in the early 2020s. We are now substantially dependent on imports, primarily from Qatar and Russia."),
sp(60),
body("Qatar shares the North Dome/South Pars gas field with Iran \u2014 the largest natural gas field in the world. Helium is a byproduct of natural gas processing. When LNG flows from the Persian Gulf are disrupted, helium flows are disrupted. When Russia\u2019s helium exports are sanctioned or restricted, the supply tightens further. The US currently faces both simultaneously."),
sp(60),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[3240,3240,3240],rows:[
  hdrRow(["Application","Why Helium Is Required","If Supply Fails"],[3240,3240,3240]),
  dataRow(["MRI machines","Superconducting magnets require liquid helium at \u22122.69\u00b0C. No substitute.","Hospitals cannot operate MRI units. Medical diagnostics compromised."],[3240,3240,3240],false),
  dataRow(["Semiconductor fab","Used to purge oxygen from chip fabrication chambers. Contamination destroys yields.","Chip production falls. Defense and consumer electronics supply chains affected."],[3240,3240,3240],true),
  dataRow(["Fiber optic cable","Required during drawing process to prevent oxidation. No substitute at scale.","Internet infrastructure expansion halts. 5G buildout slows."],[3240,3240,3240],false),
]}),
sp(80),
callout(
  "HELIUM IS A NATIONAL SECURITY INPUT, NOT A COMMODITY",
  "Every MRI machine in every rural hospital in every agricultural state runs on liquid helium. The VA hospital system uses helium for MRI diagnostics for veterans. Semiconductor fabrication for defense electronics requires helium. These are not luxury dependencies. They are operational requirements with no near-term domestic alternative. The Federal Helium Reserve that could have buffered this disruption was sold off. It cannot be rebuilt in months.",
  LNAVY, NAVY
),
sp(160),

h2("The De-dollarization Chain"),
body("Iran now accepts yuan for Strait of Hormuz passage. Japan and South Korea \u2014 US allies \u2014 are actively building yuan and euro settlement mechanisms for energy and helium purchases because they have no choice: dollar-denominated trade for essential goods now carries confiscation risk. Saudi Arabia has discussed yuan-denominated oil contracts. This infrastructure does not disappear when the Iran crisis ends. Once it achieves critical-mass network effects \u2014 estimated Q1\u2013Q4 2027 \u2014 dollar reserve status restoration becomes structurally impossible."),
sp(80),
callout(
  "THE SUEZ PARALLEL",
  "Britain achieved military success in Suez in 1956 and lost reserve currency status within months. The critical difference: in 1956, the United States imposed the correction on Britain. In 2026, the United States is the acting hegemon. There is no external correction mechanism. The market is making the correction instead.",
  LGOLD, GOLD
),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("II. Why the Current Tax System Cannot Solve This"),
body("The structural problem is not political will. It is instrument failure. The income tax system is calibrated to a 20th-century economy. Financial transaction volume \u2014 the layer where modern economic activity actually occurs \u2014 is completely invisible to it."),
sp(80),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[3240,3240,3240],rows:[
  hdrRow(["Scenario","What Income Tax Sees","What Velocity Tax Sees"],[3240,3240,3240]),
  dataRow(["Stock position traded 1,000 times, zero net price change","Zero. No gain recognized.","2,000 transaction legs. Enormous accumulated path."],[3240,3240,3240],false),
  dataRow(["High-frequency firm executing $65T notional per year","Near-zero. Gains offset losses.","$227B at 0.35% rate. Significant revenue from the financial layer."],[3240,3240,3240],true),
  dataRow(["Small business with $500K revenue and $250K payroll","$74,925 in combined taxes and compliance costs.","$2,450. A 97% reduction."],[3240,3240,3240],false),
]}),
sp(80),
body("Federal debt exceeds $36 trillion. Debt service is the fastest-growing budget line. The income tax cannot close this gap \u2014 it is procyclical by design: revenues collapse in recessions when debt pressure is highest. The velocity tax taxes V in Milton Friedman\u2019s equation MV = PQ \u2014 the path integral of monetary movement, not the productive economy. Financial transaction volume is orders of magnitude larger than GDP. A tiny rate generates revenue sufficient to replace the entire federal tax apparatus, with surplus."),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("III. The Instrument: A Single Flat Rate on Every Cleared Transaction"),
body("The velocity tax is an excise tax on every transaction that clears through the banking system. The same flat rate \u2014 0.25\u20130.7% \u2014 applied automatically at the clearing layer, like an ATM fee. No returns. No audits. No criminal liability. No offshore structures. No lobbyists writing carve-outs."),
sp(80),
bullet("Same rate on every dollar of commerce, every financial trade, every wire transfer. Government transactions included."),
bullet("Self-collecting: the clearing bank deducts it automatically. It cannot be wrong."),
bullet("Rate: 0.25\u20130.7% flat. Revenue sufficient to replace all federal taxes with surplus."),
bullet("Who pays more: high-frequency traders, private equity, hedge funds \u2014 the entities generating financial fragility. Citadel alone executes ~$65T/year in notional transactions. At 0.35%: ~$227B in velocity tax."),
bullet("Who pays far less: every American business producing goods and services. Apple saves ~$33B. Amazon ~$16.5B. A 5-employee small business saves $72,475 per year \u2014 a 97% reduction."),
sp(80),
callout(
  "NO CARVE-OUTS \u2014 FOR ANYONE",
  "The federal government\u2019s own transactions are subject to this rate. State and local government transactions are subject to this rate. Congress, the Pentagon, the Treasury \u2014 all pay. No public or private entity receives an exemption the United States government itself does not receive. When the financial sector requests a carve-out, the answer is: explain why you deserve a privilege that the US government does not have. That is a public floor vote no one wants to take.",
  LGOLD, GOLD
),
sp(80),
callout(
  "CONSTITUTIONAL BASIS: NO AMENDMENT REQUIRED",
  "The velocity tax is an excise tax under Article I, Section 8. Congress has plenary authority. The Sixteenth Amendment is irrelevant \u2014 it authorizes income taxes; this instrument has no income measurement, no adjusted gross income, no returns. Historical precedent: documentary stamp taxes, securities transaction taxes, telephone excise tax \u2014 all constitutional without amendment. Someone will file suit. The excise doctrine defeats it.",
  LNAVY, NAVY
),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("IV. Where the Revenue Goes: The American Productivity Dividend"),
body("The revenue generated by velocity taxation is large enough to replace all federal taxes and fund three programs that simultaneously solve the capital flight objection and make the United States dramatically more attractive to productive investment."),
sp(80),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[2880,3420,3420],rows:[
  hdrRow(["Program","What It Does for Workers","What It Does for Employers and the Economy"],[2880,3420,3420]),
  dataRow(["Universal healthcare","Workers free from job-lock. Can leave bad employers, take entrepreneurial risk, accept equity or part-time arrangements.","$7\u20138,000 per employee per year in overhead eliminated. H1B benefit arbitrage gone \u2014 domestic workers cost-competitive without visa restrictions."],[2880,3420,3420],false),
  dataRow(["Guaranteed income floor","The foundation from which free people make free choices. Every farmer in a bad season, every startup founder, every displaced worker has a floor.","Consumer demand stabilized. Workforce can take long-horizon productive risk. Less desperate labor negotiation means more flexible employment."],[2880,3420,3420],true),
  dataRow(["Universal pensions","Workers not trapped in jobs by retirement fear. Dynamic, flexible labor markets.","Workforce productivity over full career. Less retirement insecurity driving short-term financial decisions."],[2880,3420,3420],false),
]}),
sp(80),
body("These programs are funded first \u2014 by statute, before debt paydown. They are not aspirational. They are the primary allocation. Debt reduction is the structural consequence of the surplus after programs are fully funded. A bill that separates the programs from the instrument has removed the reason the instrument exists."),
sp(80),
callout(
  "THE CAPITAL FLIGHT ANSWER",
  "Critics argue a transaction tax triggers capital flight. The concern is valid for speculative capital \u2014 precisely the capital the instrument applies friction to. Productive capital does not flee above all else. It seeks stable consuming populations, low labor overhead, and workforce flexibility. A nation providing universal healthcare, guaranteed income, and pensions provides all three simultaneously. The velocity tax and the Productivity Dividend are not in tension. They are the same instrument working at two layers of the economy at once.",
  LGOLD, GOLD
),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("V. Transforming the IRS Into an Investment Engine"),
body("The IRS employs 87,000 people across 600+ district offices organized by geography. Its primary function is enforcing a system that ceases to exist under velocity taxation. The enforcement apparatus becomes obsolete the day the velocity tax replaces the income system. That is not a problem. It is the largest underutilized economic development infrastructure in the federal government."),
sp(80),
body("Each district office becomes a Regional Revenue Development Office. It receives an annual velocity tax revenue allocation proportional to economic activity in its district. Its mandate: deploy that revenue into productive investment and workforce retraining. Performance is measured by external federal data \u2014 BEA economic output, BLS employment in productive sectors, BLS median wage growth. Not self-reported. Not gameable."),
sp(60),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[4860,4860],rows:[
  hdrRow(["IRS Today","Revenue Development Service"],[4860,4860]),
  dataRow(["Enforces returns and audits","No returns: clearing layer self-collects"],[4860,4860],false),
  dataRow(["Extracts from the productive economy","Deploys capital into productive investment"],[4860,4860],true),
  dataRow(["Same function in every district","District mandate tied to local productive capacity"],[4860,4860],false),
  dataRow(["Adversarial relationship with businesses","Partnership with local businesses and municipalities"],[4860,4860],true),
  dataRow(["Leadership from IRS career pipeline","Leadership from development finance and infrastructure banking \u2014 statutory requirement"],[4860,4860],false),
]}),
sp(80),
callout(
  "WHAT THIS MEANS FOR AGRICULTURAL DISTRICTS",
  "A district in rural Iowa deploys its allocation into grain storage infrastructure, irrigation systems, rural broadband, and agricultural capital. A district in the southern plains deploys into cotton gin modernization, water systems, and renewable energy for farm operations. A district in Appalachia deploys into energy transition infrastructure and workforce retraining. The geographic distribution of the IRS network \u2014 built over a century to reach every community in America \u2014 becomes the delivery mechanism for the most ambitious domestic investment program in American history. The majority of American workers need periodic retraining in a rapidly changing economy. District offices are the natural delivery mechanism.",
  LGREEN, DGREEN
),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("VI. The 2026 Window \u2014 Why This Cannot Be Deferred"),
body("The Iran conflict has compressed the fiscal reform timeline from \u201csometime this decade\u201d to the next 18\u201324 months. Two lock-in points are converging:"),
sp(60),
bullet("The infrastructure point of no return: estimated Q1\u2013Q4 2027 \u2014 when yuan/energy settlement rails achieve critical-mass network effects that make dollar reserve status restoration structurally impossible. Infrastructure built to route around Iran sanctions does not disappear when the Iran crisis ends."),
bullet("The debt service threshold: when debt service exceeds ~30% of revenues, only austerity or monetization remain. Both are catastrophic. Both become politically unavoidable once the threshold is crossed."),
sp(80),
callout(
  "THE VELOCITY TAX IS NOT A RESPONSE TO THE IRAN CRISIS",
  "It is the structural fiscal reform that the Iran crisis makes impossible to defer. The crisis is the forcing function. The reform is the instrument that matches the tax base to where the economy actually lives \u2014 in the path integral of monetary movement, not in the income and consumption flows of a 20th-century economy.",
  LGOLD, GOLD
),
sp(80),
body("Immediate actions in this brief require no new legislation \u2014 they are executive authority. The pilot legislation is narrow, bipartisan-viable, and does not require full system implementation before establishing the precedent and data infrastructure. The key: the social program allocation structure must be in the pilot bill from day one, even at modest revenue levels. Establishing that precedent in the pilot is the structural prevention of the worst failure mode."),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("VII. Where This Ends If Nothing Changes"),
body("This section does not offer projections. It describes structural outcomes that follow mechanically from decisions already made and infrastructure already being built. The timeline is conservative."),
sp(80),

new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[1440,3240,5040],rows:[
  hdrRow(["Timeframe","What Happens","Why It Cannot Be Reversed"],[1440,3240,5040]),
  dataRow(["2027","Yuan/euro settlement rails for energy, helium, and agricultural goods reach critical-mass network effects. Countries that built this infrastructure to survive US sanctions now prefer it on cost and reliability grounds.","Network effects. Once a settlement system achieves liquidity, switching back to dollar settlement imposes costs on both parties. Historical precedent: sterling never recovered from Suez. No country restored the pound as reserve currency after the shift to dollar settlement."],[1440,3240,5040],false),
  dataRow(["2027\u20132028","Debt service crosses ~30% of federal revenues. At that threshold, the federal government faces a binary choice: austerity severe enough to trigger recession, or monetization (printing money to service debt) that triggers inflation. Both destroy the conditions that make dollar assets attractive.","At 30%+ debt service, there is no fiscal surplus available for productive investment. The velocity tax\u2019s debt-paydown mechanism becomes unavailable because there is no room to run it. The window for structural reform closes."],[1440,3240,5040],true),
  dataRow(["2030\u20132035","Alternative settlement infrastructure becomes the preferred route for a growing share of global commodity trade. Dollar demand falls. Dollar weakens structurally. Import costs rise for every American consumer and every business buying inputs.","This is not a crisis event. It is a gradual structural shift that compounds annually. Each year of dollar weakness increases import costs, increases inflation pressure, decreases US purchasing power in global markets. The correction becomes the new normal."],[1440,3240,5040],false),
  dataRow(["2040\u20132050","Federal debt, compounded at higher borrowing costs (a weaker dollar means higher interest demanded by foreign creditors), becomes unserviceable without sustained monetization. Social programs are cut in sequence: first discretionary, then mandatory. Defense spending competes directly with debt service.","A sovereign debt spiral is self-reinforcing: higher borrowing costs increase the deficit, which increases borrowing, which increases borrowing costs. The United States has never faced this from inside \u2014 only imposed it on others. The IMF does not have a lending facility large enough to address US sovereign debt."],[1440,3240,5040],true),
  dataRow(["2075+","The United States is a large, wealthy, domestically-focused economy that is no longer the center of global financial architecture. This is not catastrophe. It is managed decline \u2014 the British trajectory. American consumers are poorer in global terms. American institutions are less influential. American productive capacity, already hollowed out over four decades of financial extraction, does not recover.","Once the dollar is no longer the primary reserve currency, the US loses the \u2018exorbitant privilege\u2019 \u2014 the ability to run deficits financed cheaply by global demand for dollar assets. Everything the US government does becomes more expensive. Every American\u2019s standard of living relative to the rest of the world falls."],[1440,3240,5040],false),
]}),
sp(100),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({
  borders:cb(DRED),shading:{fill:LRED,type:ShadingType.CLEAR},
  margins:{top:160,bottom:160,left:360,right:360},
  width:{size:9720,type:WidthType.DXA},
  children:[
    new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"THE POINT OF NO RETURN IS NOT 2075. IT IS 2027.",color:DRED,bold:true,size:24,font:"Arial"})]}),
    new Paragraph({spacing:{before:80},children:[new TextRun({text:"The 50-year trajectory above is set in motion by decisions made in the next 18\u201324 months. The infrastructure lock-in point, the debt service threshold, and the settlement rail network effect all converge in the 2027\u20132028 window. After that window, structural reform can still reduce harm \u2014 it cannot restore what was lost. The dollar\u2019s reserve status, once gone, does not come back. The question is not whether to act. The question is whether the 2026\u20132027 Congress acts before or after the window closes.",color:BLACK,size:21,font:"Arial"})]})
  ]
})]})]}),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("VIII. The Legislative Action Plan"),
body("Ten actions. The first three require no legislation. The remainder are staged to build the institutional knowledge base and supporting coalition before the blocking coalition can organize."),
sp(80),

actionBlock("1","Treasury Velocity Study Directive","Immediate \u2014 Executive Authority","Direct Treasury to produce a 60-day study of implementing a 0.1% Automated Payment Transaction pilot on financial transactions over $1 million. CBO scoring alongside. Establishes the institutional knowledge base and forces the conversation into the legislative record before the financial sector lobby can organize against it."),
sp(40),
actionBlock("2","Federal Reserve Velocity Reporting Mandate","Immediate \u2014 Executive Authority","Amend the Fed\u2019s semi-annual Humphrey-Hawkins reporting to include quarterly real-time velocity (V) disaggregated by transaction type: productive sector vs. financial sector. This data exists in clearing systems. Making it visible to Congress is the prerequisite for accountable rate design."),
sp(40),
actionBlock("3","De-dollarization Early Warning Dashboard","Immediate \u2014 Executive Authority","Direct Treasury Intelligence and the Federal Reserve to publish a monthly dashboard: percentage of global trade settled in USD vs. alternative currencies, broken out by commodity (energy, helium, agricultural goods, rare earths). Real-time visibility into the lock-in trajectory. Establishes the baseline for the 2% tripwire in Action 7."),
sp(40),
actionBlock("4","Velocity Tax Pilot Act","30-Day Legislation","Introduce legislation establishing a 0.1% transaction tax on equity trades above $100,000, effective for a 36-month pilot period. CRITICAL: The social program allocation structure \u2014 healthcare, guaranteed income floor, universal pensions \u2014 must be in the bill from the first dollar of revenue in the first month. Not deferred to a companion bill. Not held in escrow. In the pilot from day one, even at modest scale. The precedent established in the pilot is the structural protection against social program decoupling in the permanent program. Renewal requires independent certification that social program allocations were fully funded and a distributional analysis showing positive net effect on households below median income."),
sp(40),
actionBlock("5","Dollar Reserve Protection Board","30-Day Legislation","Establish a bipartisan Dollar Reserve Protection Board with veto authority over Treasury actions affecting essential civilian resource flows \u2014 specifically helium, ammonia/fertilizer precursors, rare earths, and pharmaceutical inputs. Prevents weaponization of financial infrastructure against the goods alternative settlement systems are being built specifically to transport. If essential goods can flow in dollars, they will."),
sp(40),
actionBlock("6","Conditional Rebate \u2014 Productive Investment","30-Day Legislation","Return 5\u201310% of velocity tax revenue to financial institutions \u2014 including high-frequency trading firms, hedge funds, and private equity \u2014 conditioned on deployment into tangible productive assets: manufacturing, infrastructure, agricultural capital, domestic helium recovery infrastructure, domestic ammonia production capacity, energy systems, housing. Participation requires a designated separate account, independent certification of deployment, and full audit trail. Misuse carries criminal liability. This is not a rate carve-out: every participant pays the full flat rate. The rebate is a productive investment incentive open to any entity willing to put capital to work in the real economy."),
sp(40),
actionBlock("7","AI Monetary Management Authorization Act","90-Day Legislation","Authorize AI-managed dynamic rate adjustment operating on real-time clearing data, within parameters set by Congress and the Seventh Generation Oversight Commission. Rate formula: t(V) = t\u2080 + k \u00d7 max(0, V \u2212 V\u2080). Three-mode counter-cyclical design: Mode 1 (prosperity) builds reserves; Mode 2 (volatility) reduces friction; Mode 3 (crisis circuit breaker) applies a universal rate ceiling to all transactions \u2014 no transaction classification required, triggered by 2% de-dollarization or Fed systemic certification. Congressional override, full parameter transparency, and financial sector exclusion from oversight are mandatory provisions."),
sp(40),
actionBlock("8","Non-Dollar Clearing Protection Act","90-Day Legislation","Establish clearing arrangements for designated essential goods \u2014 helium, ammonia, rare earths, pharmaceutical precursors \u2014 that operate outside SWIFT for those specific goods. If essential goods can be settled in dollars, they will be. This ensures they can, regardless of sanctions state. Modeled on INSTEX. Prevents resource warfare from producing the permanent alternative clearing infrastructure it is meant to punish."),
sp(40),
actionBlock("9","Revenue Development Service Act","Concurrent with Implementation","Remand and rename the IRS. District offices become Regional Revenue Development Offices. Mandate: deploy velocity tax revenue into productive investment and workforce development. Statutory requirement: district leadership recruited from development finance, infrastructure banking, and community investment backgrounds \u2014 not the IRS career pipeline. Performance measured by BEA and BLS external data, not self-reported metrics."),
sp(40),
actionBlock("10","Seventh Generation Monetary Oversight Commission","Concurrent with Action 7","Establish an independent oversight body for the AI monetary management system. Seven commissioners serving 14-year staggered terms. Financial sector barred: no commissioner may have held a financial institution position within 10 years of appointment, or for 10 years following. Authority: preemptive suspension power, plain-language quarterly public reporting, circuit breaker Mode 3 trigger, federal court standing as intergenerational trustee. The Commission must exist before the system it oversees goes live."),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("IX. What Is at Stake"),
body("The generation of Americans farming today, the hospitals running MRI machines today, the semiconductor plants fabricating chips for defense systems today \u2014 they are operating inside a supply chain disruption that is not going to resolve itself when the Iran crisis ends. The infrastructure being built to route around dollar-denominated settlement is permanent. The debt trajectory is structural. The tax base is mismatched to the economy it is taxing."),
sp(80),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[4860,4860],rows:[
  hdrRow(["Current Trajectory","With This Reform"],[4860,4860]),
  dataRow(["Fertilizer costs spike with every energy disruption. Farm income volatile. Food prices follow.","Domestic ammonia production capacity built via conditional rebate. Supply chain resilience funded through district investment."],[4860,4860],false),
  dataRow(["Helium supply dependent on Qatar and Russia. Federal reserve sold off. No buffer.","Non-dollar clearing protection ensures helium flows regardless of sanctions state. Domestic recovery infrastructure funded."],[4860,4860],true),
  dataRow(["Alternative settlement rails permanent by 2027. Dollar reserve status non-restorable.","Fiscal credibility demonstrated before lock-in point. Productive capital attracted by healthcare and income security. Speculative churn dampened."],[4860,4860],false),
  dataRow(["Debt service crowds out defense, infrastructure, and social programs simultaneously.","Surplus revenue above social programs reduces sovereign debt structurally. Borrowing costs fall."],[4860,4860],true),
  dataRow(["Workers chained to employers by healthcare. Small businesses crushed by compliance. HFT pays near zero.","Universal healthcare eliminates job-lock. 97% tax reduction for small businesses. HFT pays in proportion to transaction volume."],[4860,4860],false),
]}),
sp(120),
body("This is not a long-horizon problem. The Strait of Hormuz is closed now. The settlement rails are being built now. The planting season is this spring. The window in which structural fiscal reform can prevent permanent de-dollarization is measured in months, not years."),
sp(80),
body("The velocity tax is the instrument that matches the tax base to the economy that exists today. The American Productivity Dividend is the instrument that makes the United States genuinely attractive to the productive capital the world needs to park somewhere. Together, they are the fiscal reform this moment requires.", {bold:false}),
sp(120),
new Paragraph({spacing:{before:60},children:[new TextRun({text:"Velocity tax derivation: Michael Fox, 1989. Independent parallel derivation: Edgar L. Feige (University of Wisconsin\u2013Madison), 2000. April 5, 2026.",color:MGREY,size:16,font:"Arial",italics:true})]})

    ]}]
});

Packer.toBuffer(doc).then(buf=>{
  fs.writeFileSync("reports/dollar_stability_brief_2026-04-05.docx",buf);
  console.log("Written: reports/dollar_stability_brief_2026-04-05.docx");
}).catch(e=>{console.error(e);process.exit(1);});
