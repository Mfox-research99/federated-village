const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat,
  TabStopType, TabStopPosition
} = require('docx');
const fs = require('fs');

const NAVY="1B3A5C",GOLD="B8860B",LGOLD="F5F0E0",LNAVY="E8EEF4",
      LGREEN="EAF4EA",DGREEN="2E6B2E",WHITE="FFFFFF",BLACK="1A1A1A",MGREY="555555";
const b1=(c)=>({style:BorderStyle.SINGLE,size:6,color:c});
const nb={style:BorderStyle.NONE,size:0,color:"FFFFFF"};
const noBorders={top:nb,bottom:nb,left:nb,right:nb};
const cb=(c)=>({top:b1(c),bottom:b1(c),left:b1(c),right:b1(c)});
const sp=(b=100)=>new Paragraph({spacing:{before:b,after:0},children:[new TextRun("")]});
const body=(t,o={})=>new Paragraph({spacing:{before:60,after:80},children:[new TextRun({text:t,color:o.color||BLACK,size:22,font:"Arial",bold:o.bold||false,italics:o.italic||false})]});
const h1=(t)=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:300,after:80},border:{bottom:{style:BorderStyle.SINGLE,size:4,color:GOLD}},children:[new TextRun({text:t,color:NAVY,bold:true,size:28,font:"Arial"})]});
const h2=(t,c=NAVY)=>new Paragraph({spacing:{before:180,after:60},children:[new TextRun({text:t,color:c,bold:true,size:24,font:"Arial"})]});
const bullet=(t)=>new Paragraph({numbering:{reference:"bullets",level:0},spacing:{before:40,after:40},children:[new TextRun({text:t,color:BLACK,size:22,font:"Arial"})]});
const pullquote=(t,fill=LGOLD,border=GOLD)=>new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:{top:nb,bottom:nb,right:nb,left:b1(border)},shading:{fill,type:ShadingType.CLEAR},margins:{top:120,bottom:120,left:240,right:240},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:t,color:NAVY,size:24,font:"Arial",italics:true,bold:true})]})]})]})],});
const banner=(title,body_t,fill=NAVY,titleColor=GOLD,bodyColor=WHITE)=>new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:cb(fill),shading:{fill,type:ShadingType.CLEAR},margins:{top:200,bottom:200,left:360,right:360},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:title,color:titleColor,bold:true,size:26,font:"Arial"})]}),new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[new TextRun({text:body_t,color:bodyColor,size:20,font:"Arial",italics:true})]})]})]})]});
const actionBlock=(num,title,tier,body_t)=>new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},margins:{top:60,bottom:60,left:160,right:160},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:`${num}. ${title.toUpperCase()}`,color:WHITE,bold:true,size:20,font:"Arial"}),new TextRun({text:`   [${tier}]`,color:GOLD,size:18,font:"Arial"})]})]})]}),new TableRow({children:[new TableCell({borders:cb(NAVY),shading:{fill:LNAVY,type:ShadingType.CLEAR},margins:{top:100,bottom:100,left:200,right:200},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:body_t,color:BLACK,size:21,font:"Arial"})]})]})]})],});
const dataRow=(cells,widths,shaded=false)=>new TableRow({children:cells.map((t,i)=>new TableCell({borders:cb("CCCCCC"),shading:{fill:shaded?"F5F5F5":WHITE,type:ShadingType.CLEAR},margins:{top:70,bottom:70,left:100,right:100},width:{size:widths[i],type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:t,color:BLACK,size:20,font:"Arial"})]})]}))}); 
const hdrRow=(cells,widths)=>new TableRow({children:cells.map((t,i)=>new TableCell({borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},margins:{top:70,bottom:70,left:100,right:100},width:{size:widths[i],type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:t,color:WHITE,bold:true,size:20,font:"Arial"})]})]}))}); 

const doc = new Document({
  numbering:{config:[{reference:"bullets",levels:[{level:0,format:LevelFormat.BULLET,text:"\u2022",alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:720,hanging:360}}}},{level:1,format:LevelFormat.BULLET,text:"\u25e6",alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:1080,hanging:360}}}}]}]},
  styles:{default:{document:{run:{font:"Arial",size:22,color:BLACK}}},paragraphStyles:[{id:"Heading1",name:"Heading 1",basedOn:"Normal",next:"Normal",quickFormat:true,run:{size:28,bold:true,font:"Arial",color:NAVY},paragraph:{spacing:{before:300,after:80},outlineLevel:0}}]},
  sections:[{
    properties:{page:{size:{width:12240,height:15840},margin:{top:1080,right:1260,bottom:1080,left:1260}}},
    headers:{default:new Header({children:[new Paragraph({tabStops:[{type:TabStopType.RIGHT,position:TabStopPosition.MAX}],border:{bottom:{style:BorderStyle.SINGLE,size:6,color:GOLD}},spacing:{before:0,after:80},children:[new TextRun({text:"AMERICAN PRODUCTIVITY TAX REFORM  |  LEGISLATIVE BRIEF",color:NAVY,size:16,font:"Arial"}),new TextRun({text:"\t"}),new TextRun({text:"Page ",color:MGREY,size:16,font:"Arial"}),new TextRun({children:[PageNumber.CURRENT],color:MGREY,size:16,font:"Arial"}),new TextRun({text:" of ",color:MGREY,size:16,font:"Arial"}),new TextRun({children:[PageNumber.TOTAL_PAGES],color:MGREY,size:16,font:"Arial"})]})]}),},
    footers:{default:new Footer({children:[new Paragraph({border:{top:{style:BorderStyle.SINGLE,size:4,color:NAVY}},children:[]}),new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[new TextRun({text:"American Productivity Tax Reform  \u2022  Legislative Brief  \u2022  April 5, 2026",color:MGREY,size:16,font:"Arial",italics:true})]})]})},
    children:[

// Title
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:noBorders,shading:{fill:NAVY,type:ShadingType.CLEAR},margins:{top:320,bottom:320,left:480,right:480},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"AMERICAN PRODUCTIVITY TAX REFORM",color:GOLD,bold:true,size:22,font:"Arial"})]}),new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[new TextRun({text:"A Single Rate That Replaces Them All",color:WHITE,bold:true,size:36,font:"Arial"})]}),new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:60},children:[new TextRun({text:"A Legislative Brief for the United States Congress",color:WHITE,size:22,font:"Arial"})]}),new Paragraph({alignment:AlignmentType.CENTER,border:{top:{style:BorderStyle.SINGLE,size:4,color:GOLD}},spacing:{before:80},children:[new TextRun({text:"April 5, 2026",color:GOLD,size:18,font:"Arial",italics:true})]})]})]})]}),
sp(160),

// Panel verdict banner
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:cb(GOLD),shading:{fill:LGOLD,type:ShadingType.CLEAR},margins:{top:160,bottom:160,left:360,right:360},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"READY FOR LEGISLATIVE INTRODUCTION",color:NAVY,bold:true,size:28,font:"Arial"})]}),new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:60},children:[new TextRun({text:"\u201cThe core architecture is sound, internally consistent, and constitutionally grounded. This proposal is ready.\u201d",color:NAVY,size:20,font:"Arial",italics:true})]})]})]})]}),
sp(200),

// Section I
new Paragraph({children:[new PageBreak()]}),
h1("I. What This Is"),
body("This is not a new tax on top of existing taxes. It is not a social spending proposal. It is not wealth redistribution. It is a complete replacement of the most complex, punitive, and economically destructive tax system in the developed world with a single flat rate applied automatically at the clearing layer \u2014 the same way an ATM fee works."),
sp(80),
bullet("No returns. No audits. No criminal liability for getting it wrong."),
bullet("No industry of attorneys and accountants needed to navigate it."),
bullet("No offshore subsidiary structures to exploit. No lobbyists writing carve-outs."),
bullet("Same rate on every cleared transaction \u2014 every dollar of commerce, every financial trade, every wire transfer. Government transactions included."),
sp(80),
body("Every American business \u2014 from the corner store to Apple \u2014 pays far less than today. Workers are freed from job-lock because healthcare and pensions come from the tax base, not from employers. American productive capacity is unleashed because the barriers to starting, running, and growing a business are eliminated."),
sp(80),
body("The only entities that pay more are those that generate income by moving money rather than by making things: high-frequency traders, private equity, hedge funds. Friction on speculation. Freedom for production."),
sp(80),
pullquote("This is the flat tax conservatives have wanted for decades. It is also the most significant expansion of economic security for working Americans in a century. These are not contradictory. They are the same instrument."),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("II. The Derivation"),
body("Milton Friedman\u2019s equation of exchange:"),
sp(60),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:cb(NAVY),shading:{fill:LNAVY,type:ShadingType.CLEAR},margins:{top:160,bottom:160,left:480,right:480},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"MV = PQ",color:NAVY,bold:true,size:44,font:"Arial"})]}),new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[new TextRun({text:"M = money supply  \u2022  V = velocity of money  \u2022  P = price level  \u2022  Q = real output",color:MGREY,size:18,font:"Arial"})]})]})]})]},),
sp(120),
body("Every existing tax taxes P and Q \u2014 what people make, grow, and sell. Income tax, capital gains, payroll, excise: all derivatives of the productive economy. The velocity tax taxes V: the path integral of monetary movement. The total accumulated distance money travels at every clearing event, regardless of direction or destination."),
sp(60),
body("Financial transaction volume exceeds GDP by orders of magnitude. A stock position traded 1,000 times in a day with zero net price change: income tax sees zero, capital gains sees zero, velocity tax sees 2,000 transaction legs. This is where the modern economy actually lives \u2014 and no existing tax touches it."),
sp(80),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:cb(NAVY),shading:{fill:LNAVY,type:ShadingType.CLEAR},margins:{top:120,bottom:120,left:480,right:480},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"t(V) = t\u2080 + k \u00d7 max(0, V \u2212 V\u2080)",color:NAVY,bold:true,size:32,font:"Arial"})]}),new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:60},children:[new TextRun({text:"Rate rises with excess velocity above productive baseline \u2014 self-correcting without legislative action",color:MGREY,size:18,font:"Arial"})]})]})]})]},),
sp(80),
body("Rate range: 0.25\u20130.7% flat. Revenue sufficient to replace the entire federal tax apparatus. Self-collecting at the clearing layer. Cannot be wrong. Cannot be audited.", {color:MGREY,italic:true}),
body("Attribution: Michael Fox, 1989. Independent parallel derivation: Edgar L. Feige (University of Wisconsin\u2013Madison), 2000.", {color:MGREY,italic:true}),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("III. The Math \u2014 What Every Business Saves"),
h2("Small Business (5 employees, $50K average wage, $500K revenue)"),
sp(60),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[4680,2520,2520],rows:[
  hdrRow(["Tax Item","Current System","Velocity Tax @ 0.35%"],[4680,2520,2520]),
  dataRow(["Employer FICA (7.65% of wages)","$19,125","—"],[4680,2520,2520],false),
  dataRow(["Healthcare (employer share)","$26,250","PAID \u2014 Productivity Dividend"],[4680,2520,2520],true),
  dataRow(["Workers\u2019 compensation","$7,500","—"],[4680,2520,2520],false),
  dataRow(["Federal income tax","$10,500","—"],[4680,2520,2520],true),
  dataRow(["State income tax","$2,500","—"],[4680,2520,2520],false),
  dataRow(["Compliance (accountant/payroll)","$8,000","—"],[4680,2520,2520],true),
  dataRow(["Tax on $500K sales + $200K purchases","—","$2,450"],[4680,2520,2520],false),
  new TableRow({children:[new TableCell({borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},margins:{top:80,bottom:80,left:100,right:100},width:{size:4680,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:"TOTAL ANNUAL TAX BURDEN",color:WHITE,bold:true,size:20,font:"Arial"})]})]}),new TableCell({borders:cb(NAVY),shading:{fill:LGOLD,type:ShadingType.CLEAR},margins:{top:80,bottom:80,left:100,right:100},width:{size:2520,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:"$74,925",color:NAVY,bold:true,size:20,font:"Arial"})]})]}),new TableCell({borders:cb(NAVY),shading:{fill:LGREEN,type:ShadingType.CLEAR},margins:{top:80,bottom:80,left:100,right:100},width:{size:2520,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:"$2,450",color:DGREEN,bold:true,size:20,font:"Arial"})]})]})]}),
  new TableRow({children:[new TableCell({borders:cb(DGREEN),shading:{fill:LGREEN,type:ShadingType.CLEAR},colSpan:3,margins:{top:80,bottom:80,left:200,right:200},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"NET SAVING: $72,475 per year  \u2014  97% reduction  \u2014  Criminal liability: ELIMINATED",color:DGREEN,bold:true,size:22,font:"Arial"})]})]})]})
]}),
sp(120),
pullquote("The velocity tax cannot be wrong. There is nothing to audit. There is no criminal liability. That alone is worth an enormous amount to any small business owner."),
sp(160),
h2("5-Tier Supply Chain vs. Amazon (same $1,000 product)"),
sp(60),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[3600,2040,2040,2040],rows:[
  hdrRow(["Supply Chain Tier","Revenue","Current Taxes","Velocity Tax"],[3600,2040,2040,2040]),
  dataRow(["Raw materials supplier","$100","$14.99","$0.53"],[3600,2040,2040,2040],false),
  dataRow(["Parts processor","$250","$37.46","$1.23"],[3600,2040,2040,2040],true),
  dataRow(["Component assembler","$450","$67.43","$2.45"],[3600,2040,2040,2040],false),
  dataRow(["Final assembler","$700","$104.89","$4.03"],[3600,2040,2040,2040],true),
  dataRow(["Distributor / retailer","$1,000","$149.85","$5.95"],[3600,2040,2040,2040],false),
  new TableRow({children:["TOTAL CHAIN","","$374.62","$14.18"].map((t,i)=>new TableCell({borders:cb(NAVY),shading:{fill:i===2?LGOLD:i===3?LGREEN:LNAVY,type:ShadingType.CLEAR},margins:{top:70,bottom:70,left:100,right:100},width:{size:[3600,2040,2040,2040][i],type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:t,color:i===2?"B8860B":i===3?DGREEN:NAVY,bold:true,size:20,font:"Arial"})]})]}))})
]}),
sp(80),
body("Current taxes are 26\u00d7 larger than velocity tax across the full chain. Amazon vs. small chain: today\u2019s system disadvantages the small chain by $254.62 per $1,000 of product. Under velocity tax: $10.68. A 24\u00d7 improvement in competitive position."),
sp(160),
h2("Large Corporations \u2014 Annual Tax Savings"),
sp(60),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[2880,1920,1920,1920,1080],rows:[
  hdrRow(["Company","Current Burden","Velocity Tax","Net Saving","Reduction"],[2880,1920,1920,1920,1080]),
  dataRow(["Apple Inc.","$35.6B","$2.3B","$33.3B","94%"],[2880,1920,1920,1920,1080],false),
  dataRow(["Amazon","$20.3B","$3.7B","$16.5B","82%"],[2880,1920,1920,1920,1080],true),
  dataRow(["Home Depot","$8.9B","$0.9B","$8.1B","90%"],[2880,1920,1920,1920,1080],false),
  dataRow(["Walmart","$21.1B","$4.0B","$17.2B","81%"],[2880,1920,1920,1920,1080],true),
  dataRow(["ExxonMobil","$19.1B","$2.5B","$16.7B","87%"],[2880,1920,1920,1920,1080],false),
  new TableRow({children:["COMBINED (5 cos.)","$105.0B","$13.3B","$91.7B","87%"].map((t,i)=>new TableCell({borders:cb(NAVY),shading:{fill:i===3?LGOLD:LNAVY,type:ShadingType.CLEAR},margins:{top:80,bottom:80,left:100,right:100},width:{size:[2880,1920,1920,1920,1080][i],type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:t,color:i===3?GOLD:NAVY,bold:true,size:20,font:"Arial"})]})]}))})
]}),
sp(80),
body("Who pays more: HFT firms, private equity, hedge funds. Citadel alone executes ~$65T/year in notional transactions. At 0.35%: ~$227B in velocity tax against near-zero income taxes today. These are the only entities facing a higher burden \u2014 and they are exactly the entities generating the financial fragility this instrument is designed to dampen."),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("IV. The American Productivity Dividend"),
body("Prior versions called this the \u201csocial dividend.\u201d The name obscured what it actually is: the direct return to every American from the productivity of the economy they contribute to. It is not a government benefit. It is infrastructure for a productive economy \u2014 the same logic as roads, power grids, and internet access."),
sp(80),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[3240,6480],rows:[
  hdrRow(["Component","What It Does"],[3240,6480]),
  dataRow(["Universal healthcare","Eliminates $7\u20138K/employee/year employer overhead. Workers freed from job-lock. Entrepreneurship enabled. H1B benefit arbitrage eliminated \u2014 domestic workers cost-competitive."],[3240,6480],false),
  dataRow(["Guaranteed income floor","Not dependency \u2014 the foundation from which free people make free choices. Every startup founder, farmer in a bad season, or displaced worker has a floor they cannot fall through."],[3240,6480],true),
  dataRow(["Universal pensions","Workers not trapped in bad jobs by fear of retirement insecurity. More dynamic, flexible labor markets. Workforce can take long-horizon productive risk."],[3240,6480],false),
]}),
sp(80),
pullquote("Stop taxing work. Start taxing money-moving. Workers earn the Dividend through the productivity of the economy they contribute to. It is earned, distributed, and self-sustaining."),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("V. The Dollar and National Security"),
body("The dollar\u2019s reserve status is not an entitlement. Japan and South Korea are building yuan/euro settlement mechanisms for energy and helium. Saudi Arabia has discussed yuan-denominated oil contracts. Iran now accepts yuan for Strait of Hormuz passage. This infrastructure does not disappear when the Iran crisis ends."),
sp(80),
bullet("2027 lock-in point: when alternative settlement rails achieve critical-mass network effects, dollar reserve restoration becomes thermodynamically impossible"),
bullet("2028 debt service threshold: when debt service exceeds ~30% of revenues, only austerity or monetization remain \u2014 both devastating"),
bullet("Suez parallel: Britain won militarily in 1956 and lost reserve currency status within months. The US is now the acting hegemon. There is no external correction mechanism."),
sp(80),
pullquote("The velocity tax is not a response to the Iran crisis. It is the structural fiscal reform that the Iran crisis makes impossible to defer."),
sp(100),
body("Three stabilization mechanisms: fiscal credibility (debt reduction from revenue surplus); productive capital attraction (the Productivity Dividend makes the US the best place to build); speculative friction (dampens financial volatility that prices instability into currency markets)."),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("VI. The Three-Mode Counter-Cyclical Rate"),
body("From sound commercial banking practice: \u201cMy job was to be counter-cyclical \u2014 lend when things were tough, retract and build capital when things were good.\u201d The velocity tax dynamic rate encodes this principle for the entire fiscal system."),
sp(80),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[1800,2640,2640,2640],rows:[
  hdrRow(["Mode","Condition","Rate","Effect"],[1800,2640,2640,2640]),
  dataRow(["1 \u2014 Prosperity","V above baseline, stable growth","Rises above t\u2080","Build reserves: debt paydown, banks build strategic capital (minerals, gold, foreign currency)"],[1800,2640,2640,2640],false),
  dataRow(["2 \u2014 Volatility","Elevated V, uncertain conditions","At or below t\u2080","Supports liquidity. Productive commerce continues. Uncertainty doesn\u2019t tip to crisis."],[1800,2640,2640,2640],true),
  dataRow(["3 \u2014 Circuit Breaker","2% de-dollarization trigger OR Fed systemic certification","Universal rate ceiling, all transactions","30/60/90-day halt. No transaction classification. Everything slows \u2014 including the flight. Auto-resets."],[1800,2640,2640,2640],false),
]}),
sp(100),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:{top:nb,bottom:nb,right:nb,left:b1(DGREEN)},shading:{fill:LGREEN,type:ShadingType.CLEAR},margins:{top:100,bottom:100,left:240,right:240},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:"PANEL VERDICT ON MODE 3: UNANIMOUSLY RESOLVED",color:DGREEN,bold:true,size:20,font:"Arial"})]}),new Paragraph({spacing:{before:60},children:[new TextRun({text:"The universal circuit breaker applies a uniform rate ceiling to all transactions during a certified crisis \u2014 no intent-based classification required. The analogy to financial market trading halts is legally and operationally sound. The design is counter-cyclical, self-resetting, and does not require surveillance infrastructure that does not exist.",color:BLACK,size:20,font:"Arial",italics:true})]})]})]})]}),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("VII. Constitutional Architecture"),
body("The velocity tax is an excise tax on transaction events. Congress has plenary authority under Article I, Section 8. The Sixteenth Amendment is irrelevant \u2014 it authorizes income taxes; this instrument has no income measurement, no adjusted gross income, no returns. It is not an income tax."),
sp(60),
bullet("Historical precedent: documentary stamp taxes, securities transaction taxes, telephone excise tax \u2014 all Constitutional without amendment"),
bullet("State baseline guarantee: current state and local revenue baseline guaranteed as statutory allocation. States lose nothing."),
bullet("Government transparency bonus: all transactions including government captured at clearing layer. Congress gains real-time visibility into every agency\u2019s spending, where and to whom. Never before available."),
bullet("Legal challenges (someone will always sue): Direct Tax Apportionment \u2014 excise doctrine defeats it; Intergovernmental Immunity \u2014 South Carolina v. Baker (1988) defeats it. Both are litigable; both lose on modern precedent."),
bullet("Personal transaction floor: a threshold for non-commercial person-to-person transfers (under $1,000) addresses Due Process concerns without creating gaming opportunity."),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("VIII. The Revenue Development Service"),
body("The IRS enforcement function becomes obsolete when there are no returns to file and no avoidance to audit. The velocity tax is self-collecting \u2014 deducted at the clearing layer automatically. What remains is the infrastructure: 87,000 people and 600+ district offices, geographically distributed, with deep knowledge of local economies."),
sp(80),
body("Transformation: each district office becomes a Regional Revenue Development Office. Mandate: deploy velocity tax revenue allocation into productive investment and workforce retraining. Performance measured by external federal data \u2014 BEA economic output, BLS employment in productive sectors, BLS median wage growth. Not self-reported. Not gameable at the district level."),
sp(80),
body("Leadership recruited from development finance, infrastructure banking, and community investment \u2014 not the IRS career pipeline. Statutory requirement. The majority of American workers need periodic retraining in a rapidly changing economy. District offices are the delivery mechanism for that \u2014 human productive capacity alongside physical infrastructure."),
sp(80),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:{top:nb,bottom:nb,right:nb,left:b1(GOLD)},shading:{fill:LGOLD,type:ShadingType.CLEAR},margins:{top:100,bottom:100,left:240,right:240},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:"ONE REMAINING DRAFTING TASK (GLM-5 panel note):",color:NAVY,bold:true,size:20,font:"Arial"})]}),new Paragraph({spacing:{before:60},children:[new TextRun({text:"The RDS requires one additional legislative section \u2014 an operational charter specifying investment decision authority, coordination protocols with Commerce, Energy, Agriculture, and Labor, and the 87,000-employee conversion timeline. This is a drafting task for committee markup, not a structural redesign.",color:BLACK,size:20,font:"Arial"})]})]})]})]}),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("IX. The 10-Component Architecture"),
body("The complete legislative package. Each component corresponds to a specific gap in the current system."),
sp(80),
actionBlock("1","Single Tax","Article I, \u00a78 \u2014 No Amendment Required","Transaction excise tax replaces all federal taxes: income, capital gains, payroll, excise. Flat rate. Self-collecting at clearing layer. No returns. No audits. No criminal liability."),sp(40),
actionBlock("2","American Productivity Dividend","Primary Allocation \u2014 Funded First","Universal healthcare, guaranteed income floor, universal pensions. Statutory allocation \u2014 not discretionary. Funded before debt paydown. A bill that removes this ordering removes the purpose of the instrument."),sp(40),
actionBlock("3","State Baseline Guarantee","Concurrent with Implementation","Current state and local revenue guaranteed as statutory allocation. Real-time government spending transparency gained as structural consequence."),sp(40),
actionBlock("4","Sovereign Debt Paydown","Revenue Surplus","Surplus above Dividend and reserve fund reduces federal debt. Fiscal credibility rises. Dollar stabilizes structurally."),sp(40),
actionBlock("5","Conditional Rebate","5\u201310% Returned for Productive Investment","Revenue returned to financial institutions conditioned on deployment into: manufacturing, infrastructure, minerals, energy, housing, strategic reserves (gold, foreign currency, critical minerals)."),sp(40),
actionBlock("6","Revenue Development Service","IRS Transformation","87,000 employees, 600+ district offices, remandated. Deploys velocity tax revenue into productive investment and workforce development. Measured by BEA/BLS external data."),sp(40),
actionBlock("7","Seventh Generation Oversight Commission","14-Year Terms \u2014 Financial Sector Barred","Seven commissioners. No financial sector affiliation (10 years before/after). Preemptive authority. Circuit breaker Mode 3 trigger. Plain-language quarterly public reports. Federal court standing as intergenerational trustee."),sp(40),
actionBlock("8","Three-Mode Rate","Counter-Cyclical by Design","Prosperity: rate rises, build reserves. Volatility: rate falls, support liquidity. Crisis: universal circuit breaker \u2014 no transaction classification. Auto-resets after 30/60/90 days."),sp(40),
actionBlock("9","Government Transparency","Built Into Architecture","All cleared transactions \u2014 including federal, state, and local government \u2014 captured. Real-time congressional visibility into every agency\u2019s spending. First time in US history."),sp(40),
actionBlock("10","Citizen Visibility","Quarterly + Annual","Quarterly statements to all account-holders showing velocity tax paid and real-world equivalency. Public dashboards. Annual Fiscal Visibility Report auto-triggers congressional hearing if revenue exceeds Dividend allocation."),

sp(200),
new Paragraph({children:[new PageBreak()]}),
h1("X. The Single Risk Legislators Must Watch"),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},margins:{top:200,bottom:200,left:360,right:360},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"EXEMPTION CREEP",color:GOLD,bold:true,size:26,font:"Arial"})]}),new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[new TextRun({text:"The entities facing a net tax increase \u2014 high-frequency traders, certain financial intermediaries \u2014 possess sophisticated lobbying power and will immediately seek carve-outs, volume thresholds, or rebates. Any exemption breaches the structural integrity of the system and invites a cascade of complexity that would recreate the very morass this reform seeks to replace.",color:WHITE,size:21,font:"Arial",italics:true})]}),new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[new TextRun({text:"Uniformity is the reform. Defending uniformity is defending everything.",color:GOLD,bold:true,size:22,font:"Arial"})]})]})]})]}),

sp(160),
h1("What 2166 Inherits"),
new Table({width:{size:9720,type:WidthType.DXA},columnWidths:[9720],rows:[new TableRow({children:[new TableCell({borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},margins:{top:240,bottom:240,left:400,right:400},width:{size:9720,type:WidthType.DXA},children:[new Paragraph({children:[new TextRun({text:"\u201cFor the generation born in 2166: if implemented as written, they inherit a fiscal architecture severed from the 20th-century logic of taxing income and profit. Instead, they inherit a self-correcting system that taxes monetary velocity, automatically funding a universal baseline of health, income, and infrastructure. They inherit a state whose primary revenue instrument is a neutral clearing-layer excise, whose counter-cyclical stabilizer is a universal circuit breaker, and whose transformative agency is a network of regional development banks born from the ashes of the IRS.",color:WHITE,size:21,font:"Arial",italics:true})]}),new Paragraph({spacing:{before:80},children:[new TextRun({text:"It is a bet that simplicity, universality, and real-time adjustment are more resilient foundations for a 22nd-century republic than the complex, discriminatory, and politically corrosive system it replaces.\u201d",color:WHITE,size:21,font:"Arial",italics:true})]}),]})]})]}),

sp(120),
new Paragraph({spacing:{before:60},children:[new TextRun({text:"Velocity tax derivation: Michael Fox, 1989. Independent parallel derivation: Edgar L. Feige (University of Wisconsin\u2013Madison), 2000. April 5, 2026.",color:MGREY,size:16,font:"Arial",italics:true})]})


]}]});

Packer.toBuffer(doc).then(buf=>{
  fs.writeFileSync("reports/american_productivity_tax_reform_2026-04-05.docx",buf);
  console.log("Written: reports/american_productivity_tax_reform_2026-04-05.docx");
}).catch(e=>{console.error(e);process.exit(1);});
