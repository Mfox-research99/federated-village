const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat
} = require('docx');
const fs = require('fs');

const NAVY   = "1B3A5C";
const RED    = "8B1A1A";
const LRED   = "FDF0F0";
const GOLD   = "B8860B";
const LGOLD  = "F5F0E0";
const LNAVY  = "E8EEF4";
const LGREEN = "EAF4EA";
const DGREEN = "2E6B2E";
const WHITE  = "FFFFFF";
const BLACK  = "1A1A1A";
const MGREY  = "555555";

const b1 = (c) => ({ style: BorderStyle.SINGLE, size: 6, color: c });
const nb  = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: nb, bottom: nb, left: nb, right: nb };
const cb  = (c) => ({ top: b1(c), bottom: b1(c), left: b1(c), right: b1(c) });

const sp = (before=120) => new Paragraph({ spacing:{before,after:0}, children:[new TextRun("")] });

const body = (text, opts={}) => new Paragraph({
  spacing:{before:60,after:100},
  children:[new TextRun({ text, color:opts.color||BLACK, size:22, font:"Arial",
    bold:opts.bold||false, italics:opts.italic||false })]
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing:{before:320,after:100},
  border:{bottom:{style:BorderStyle.SINGLE,size:4,color:GOLD}},
  children:[new TextRun({text,color:NAVY,bold:true,size:28,font:"Arial"})]
});

const h2 = (text, color=NAVY) => new Paragraph({
  spacing:{before:200,after:80},
  children:[new TextRun({text,color,bold:true,size:24,font:"Arial"})]
});

const label = (text,color=GOLD) => new Paragraph({
  spacing:{before:280,after:60},
  children:[new TextRun({text:text.toUpperCase(),color,bold:true,size:18,font:"Arial"})]
});

const bullet = (text, bold=false) => new Paragraph({
  numbering:{reference:"bullets",level:0}, spacing:{before:40,after:40},
  children:[new TextRun({text,color:BLACK,size:22,font:"Arial",bold})]
});

const subbullet = (text, bold=false) => new Paragraph({
  numbering:{reference:"bullets",level:1}, spacing:{before:30,after:30},
  children:[new TextRun({text,color:BLACK,size:21,font:"Arial",bold})]
});

const numbered = (text) => new Paragraph({
  numbering:{reference:"numbers",level:0}, spacing:{before:60,after:60},
  children:[new TextRun({text,color:BLACK,size:22,font:"Arial"})]
});

const pullquote = (text, fill=LGOLD, border=GOLD) =>
  new Table({
    width:{size:9720,type:WidthType.DXA}, columnWidths:[9720],
    rows:[new TableRow({children:[new TableCell({
      borders:{top:nb,bottom:nb,right:nb,left:b1(border)},
      shading:{fill,type:ShadingType.CLEAR},
      margins:{top:120,bottom:120,left:240,right:240},
      width:{size:9720,type:WidthType.DXA},
      children:[new Paragraph({children:[
        new TextRun({text,color:NAVY,size:24,font:"Arial",italics:true,bold:true})
      ]})]
    })]})],
  });

const warningBox = (title, body_text) =>
  new Table({
    width:{size:9720,type:WidthType.DXA}, columnWidths:[9720],
    rows:[
      new TableRow({children:[new TableCell({
        borders:cb(RED), shading:{fill:RED,type:ShadingType.CLEAR},
        margins:{top:60,bottom:60,left:160,right:160},
        width:{size:9720,type:WidthType.DXA},
        children:[new Paragraph({children:[
          new TextRun({text:title.toUpperCase(), color:WHITE,bold:true,size:20,font:"Arial"}),
        ]})]
      })]}),
      new TableRow({children:[new TableCell({
        borders:cb(RED), shading:{fill:LRED,type:ShadingType.CLEAR},
        margins:{top:120,bottom:120,left:200,right:200},
        width:{size:9720,type:WidthType.DXA},
        children:[new Paragraph({children:[new TextRun({text:body_text,color:BLACK,size:22,font:"Arial"})]})]
      })]})
    ]
  });

const safeguardBox = (title, body_text) =>
  new Table({
    width:{size:9720,type:WidthType.DXA}, columnWidths:[9720],
    rows:[
      new TableRow({children:[new TableCell({
        borders:cb(DGREEN), shading:{fill:DGREEN,type:ShadingType.CLEAR},
        margins:{top:60,bottom:60,left:160,right:160},
        width:{size:9720,type:WidthType.DXA},
        children:[new Paragraph({children:[
          new TextRun({text:title.toUpperCase(), color:WHITE,bold:true,size:20,font:"Arial"}),
        ]})]
      })]}),
      new TableRow({children:[new TableCell({
        borders:cb(DGREEN), shading:{fill:LGREEN,type:ShadingType.CLEAR},
        margins:{top:120,bottom:120,left:200,right:200},
        width:{size:9720,type:WidthType.DXA},
        children:[new Paragraph({children:[new TextRun({text:body_text,color:BLACK,size:22,font:"Arial"})]})]
      })]})
    ]
  });

const redlineRow = (item, protect) =>
  new TableRow({children:[
    new TableCell({borders:cb("CCCCCC"),shading:{fill:LRED,type:ShadingType.CLEAR},
      margins:{top:80,bottom:80,left:120,right:120},width:{size:3480,type:WidthType.DXA},
      children:[new Paragraph({children:[new TextRun({text:item,bold:true,color:RED,size:20,font:"Arial"})]})] }),
    new TableCell({borders:cb("CCCCCC"),shading:{fill:WHITE,type:ShadingType.CLEAR},
      margins:{top:80,bottom:80,left:120,right:120},width:{size:6240,type:WidthType.DXA},
      children:[new Paragraph({children:[new TextRun({text:protect,color:BLACK,size:20,font:"Arial"})]})] }),
  ]});

const doc = new Document({
  numbering:{config:[
    {reference:"bullets",levels:[
      {level:0,format:LevelFormat.BULLET,text:"\u2022",alignment:AlignmentType.LEFT,
        style:{paragraph:{indent:{left:720,hanging:360}}}},
      {level:1,format:LevelFormat.BULLET,text:"\u25e6",alignment:AlignmentType.LEFT,
        style:{paragraph:{indent:{left:1080,hanging:360}}}},
    ]},
    {reference:"numbers",levels:[
      {level:0,format:LevelFormat.DECIMAL,text:"%1.",alignment:AlignmentType.LEFT,
        style:{paragraph:{indent:{left:720,hanging:360}}}},
    ]},
  ]},
  styles:{
    default:{document:{run:{font:"Arial",size:22,color:BLACK}}},
    paragraphStyles:[
      {id:"Heading1",name:"Heading 1",basedOn:"Normal",next:"Normal",quickFormat:true,
        run:{size:28,bold:true,font:"Arial",color:NAVY},
        paragraph:{spacing:{before:320,after:100},outlineLevel:0}},
    ]
  },
  sections:[{
    properties:{page:{size:{width:12240,height:15840},margin:{top:1080,right:1260,bottom:1080,left:1260}}},
    headers:{
      default:new Header({children:[
        new Table({
          width:{size:9720,type:WidthType.DXA}, columnWidths:[7200,2520],
          rows:[new TableRow({children:[
            new TableCell({borders:noBorders,width:{size:7200,type:WidthType.DXA},
              children:[new Paragraph({children:[new TextRun({text:"PRIVATE — FOR ALLIED LEGISLATORS  |  VELOCITY TAXATION IMPLEMENTATION SAFEGUARDS  |  APRIL 5, 2026",color:RED,size:16,font:"Arial",bold:true})]})] }),
            new TableCell({borders:noBorders,width:{size:2520,type:WidthType.DXA},
              children:[new Paragraph({alignment:AlignmentType.RIGHT,children:[
                new TextRun({text:"Page ",color:MGREY,size:16,font:"Arial"}),
                new TextRun({children:[PageNumber.CURRENT],color:MGREY,size:16,font:"Arial"}),
                new TextRun({text:" of ",color:MGREY,size:16,font:"Arial"}),
                new TextRun({children:[PageNumber.TOTAL_PAGES],color:MGREY,size:16,font:"Arial"}),
              ]})] }),
          ]})]
        }),
        new Paragraph({border:{bottom:{style:BorderStyle.SINGLE,size:6,color:RED}},children:[]})
      ]})
    },
    footers:{
      default:new Footer({children:[
        new Paragraph({border:{top:{style:BorderStyle.SINGLE,size:4,color:NAVY}},children:[]}),
        new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[
          new TextRun({text:"Federated Village Project  |  Not for public distribution  |  April 5, 2026",color:MGREY,size:16,font:"Arial",italics:true})
        ]})
      ]})
    },
    children:[

      // CONFIDENTIAL banner
      new Table({
        width:{size:9720,type:WidthType.DXA},columnWidths:[9720],
        rows:[new TableRow({children:[new TableCell({
          borders:cb(RED),shading:{fill:RED,type:ShadingType.CLEAR},
          margins:{top:180,bottom:180,left:480,right:480},
          width:{size:9720,type:WidthType.DXA},
          children:[
            new Paragraph({alignment:AlignmentType.CENTER,children:[
              new TextRun({text:"PRIVATE MEMORANDUM",color:WHITE,bold:true,size:20,font:"Arial"})
            ]}),
            new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[
              new TextRun({text:"Velocity Taxation: Implementation Safeguards",color:WHITE,bold:true,size:36,font:"Arial"})
            ]}),
            new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:60,after:60},children:[
              new TextRun({text:"What Legislators Who Support This Proposal Must Protect",color:"FFD700",bold:true,size:24,font:"Arial"})
            ]}),
            new Paragraph({alignment:AlignmentType.CENTER,border:{top:{style:BorderStyle.SINGLE,size:4,color:"FFD700"}},spacing:{before:100},children:[
              new TextRun({text:"For allied legislators only  \u2022  Not for public distribution  \u2022  April 5, 2026",color:"FFD700",size:18,font:"Arial",italics:true})
            ]}),
          ]
        })]})],
      }),

      sp(200),

      // Purpose
      new Table({
        width:{size:9720,type:WidthType.DXA},columnWidths:[9720],
        rows:[new TableRow({children:[new TableCell({
          borders:{top:nb,bottom:nb,right:nb,left:b1(NAVY)},
          shading:{fill:LNAVY,type:ShadingType.CLEAR},
          margins:{top:100,bottom:100,left:240,right:240},
          width:{size:9720,type:WidthType.DXA},
          children:[
            new Paragraph({children:[new TextRun({text:"PURPOSE OF THIS MEMORANDUM",color:NAVY,bold:true,size:20,font:"Arial"})]}),
            new Paragraph({spacing:{before:60},children:[new TextRun({text:"The velocity tax proposal has genuine transformative potential. It also carries a specific risk that is rarely discussed openly: it can be captured and turned into precisely the opposite of what it is designed to accomplish. This memo names that risk directly, describes the four ways it manifests in legislative process, and specifies the statutory provisions that must be protected. A legislator who supports this proposal but does not protect these provisions is supporting the weaponized version without knowing it.",color:BLACK,size:20,font:"Arial"})]}),
          ]
        })]})],
      }),

      sp(200),

      // Section I
      h1("I. The Core Principle"),
      body("Velocity taxation is structurally progressive by design: wealthy money travels farther by orders of magnitude, so a flat rate applied to all cleared transactions extracts proportionally far more from speculative capital than from a grocery purchase. A household spending $60,000 per year on consumption generates perhaps $120,000 in annual cleared transactions. A hedge fund executing high-frequency equity trades generates trillions. The same 0.35% rate bears entirely differently on each."),
      sp(80),
      pullquote("The proposal\u2019s primary purpose is not debt paydown. It is the social dividend: universal healthcare, a guaranteed income floor, and universal pensions for every American. Debt paydown is the structural consequence that makes the instrument politically durable. Social programs are the reason it exists."),
      sp(120),
      body("Without the social dividend, velocity taxation is a regressive instrument: a flat tax on all economic activity whose revenue flows to bondholders via debt service. The design feature that makes it transformative is also the design feature that is most vulnerable to legislative stripping. This memo addresses that vulnerability directly."),

      sp(200),

      // Section II
      new Paragraph({children:[new PageBreak()]}),
      h1("II. The Four Failure Modes"),
      body("Each of these has a historical precedent in US tax legislation. None requires malice \u2014 each can result from ordinary legislative negotiation without allies present to hold the line."),
      sp(120),

      warningBox(
        "FAILURE MODE 1: THRESHOLD CREEP",
        "The pilot begins with transactions over $1 million (equity trades over $100,000). This is the politically viable starting point: it only touches the financial sector. In subsequent legislative cycles, the threshold gets lowered \u2014 first to $10,000, then to $1,000, eventually to all consumer transactions. Each step appears modest. The cumulative result is a flat tax on every economic act, hitting the poor and middle class proportionally as hard as speculative traders. The social dividend, if it exists at all by this point, does not keep pace."
      ),
      sp(120),

      warningBox(
        "FAILURE MODE 2: SOCIAL PROGRAM DECOUPLING",
        "The velocity tax passes as a standalone fiscal reform. The social dividend \u2014 healthcare, guaranteed income, pensions \u2014 is deferred to a \u2018second bill\u2019 that will be \u2018taken up shortly.\u2019 The second bill never passes. The velocity tax revenue flows to debt paydown. Bondholders, who are disproportionately wealthy, receive the benefit of lower debt service costs. The working population bears the transaction friction with no corresponding benefit. This is the exact outcome the proposal is designed to prevent."
      ),
      sp(120),

      warningBox(
        "FAILURE MODE 3: PARAMETER CAPTURE",
        "The velocity tax passes with proper social program allocation. But the key parameters \u2014 V\u2080 (productive velocity baseline), k (dampening coefficient), and t-bounds (rate range) \u2014 are set through a rulemaking process in which financial sector participants have disproportionate influence. V\u2080 is set high enough that most speculative trading falls \u2018within productive baseline\u2019 and pays only the minimum rate. The tax becomes, in practice, a modest flat fee on all transactions, generating insufficient revenue to fund the social programs, which are then cut as \u2018underfunded.\u2019"
      ),
      sp(120),

      warningBox(
        "FAILURE MODE 4: SUNSET WITHOUT RENEWAL",
        "The 36-month pilot generates revenue and data. During the pilot, the financial sector lobbies intensively against renewal. CBO analysis is contested by financial industry-funded think tanks. The sunset clause triggers and the program expires. The social programs funded during the pilot are either discontinued (political damage) or transferred to deficit spending (restoring the structural problem the velocity tax was designed to solve). The only permanent beneficiary was the debt paydown that occurred during the pilot."
      ),
      sp(120),

      warningBox(
        "FAILURE MODE 5: STRUCTURAL EXEMPTION (EXEMPTION CREEP)",
        "The financial sector lobby requests \u2018temporary\u2019 exemptions for \u2018liquidity-critical\u2019 instruments: repo markets, interbank lending, currency swaps, derivatives clearing. Each exemption has a plausible-sounding justification \u2014 systemic risk, market function, international competitiveness. Each is granted separately, in conference or rulemaking, without a floor vote on the combined effect. The cumulative result: the highest-volume speculative transactions \u2014 exactly the ones the instrument is designed to tax \u2014 are exempt. What remains is a flat excise on productive commerce. The revenue base collapses. Social programs are cut as underfunded. The instrument has been structurally inverted. Note: the justification for each carve-out is always available. There is no instrument that cannot be argued as \u2018systemic.\u2019 Uniformity is not a design preference \u2014 it is the constitutional and economic load-bearing wall. The moment one exemption exists, every sector has an equivalent argument and the wall comes down."
      ),

      sp(200),

      // Section III
      new Paragraph({children:[new PageBreak()]}),
      h1("III. The Non-Negotiable Statutory Package"),
      body("The following five provisions must survive conference intact. Each corresponds to a specific failure mode. Losing any one of them converts the proposal from transformative to harmful."),
      sp(120),

      safeguardBox(
        "SAFEGUARD 1: STATUTORY ALLOCATION LOCK (vs. Failure Mode 2)",
        "The revenue allocation is not discretionary. The enabling legislation must specify: (1) social programs receive first priority in revenue allocation \u2014 healthcare, guaranteed income, and universal pensions funded before any other use; (2) a reserve fund receives second priority; (3) debt paydown receives the surplus after (1) and (2) are fully funded. This ordering is not advisory. It is statutory. A bill that removes this ordering has removed the purpose of the instrument."
      ),
      sp(120),

      safeguardBox(
        "SAFEGUARD 2: THRESHOLD FLOOR WITH SUPERMAJORITY REQUIREMENT (vs. Failure Mode 1)",
        "The minimum transaction threshold below which the velocity tax does not apply is established in the enabling legislation at $10,000 for consumer transactions and $100,000 for all other transactions. Lowering this threshold requires a two-thirds supermajority vote in both chambers \u2014 not ordinary legislation. This prevents threshold creep through simple majority horse-trading. Any proposal to lower the threshold without a corresponding increase in social program funding and a new CBO distributional analysis is not fiscal reform. It is redistribution upward."
      ),
      sp(120),

      safeguardBox(
        "SAFEGUARD 3: FINANCIAL SECTOR EXCLUSION FROM OVERSIGHT (vs. Failure Mode 3)",
        "The Seventh Generation Monetary Oversight Commission (Action 10 of the legislative plan) is explicitly barred from financial sector participation \u2014 not as a preference, but as a statutory disqualification. Any person employed by, compensated by, or holding significant equity in any financial institution within 7 years prior to appointment is ineligible. This provision must be in the enabling legislation, not in the Commission\u2019s operating rules, where it can be amended by the Commission itself. Parameter setting through notice-and-comment rulemaking with financial sector exclusion is the structural prevention of capture."
      ),
      sp(120),

      safeguardBox(
        "SAFEGUARD 4: RENEWAL WITH INDEPENDENT CERTIFICATION (vs. Failure Mode 4)",
        "The 36-month pilot renews only upon affirmative vote, with two required conditions: (1) an independent certification \u2014 by an entity that is not Treasury, not the Fed, and not CBO \u2014 that the social program allocations were fully funded and actually deployed during the pilot; and (2) a distributional impact analysis showing that the net effect on households below the median income is positive. If either condition is not met, the sunset triggers automatically and cannot be waived by executive action. This makes the social dividend inseparable from the instrument\u2019s continuation."
      ),
      sp(120),

      safeguardBox(
        "SAFEGUARD 5: STATUTORY PROHIBITION ON INSTRUMENT-SPECIFIC EXEMPTIONS (vs. Failure Mode 5)",
        "The enabling legislation must include an explicit prohibition: no transaction type, financial instrument, market sector, or counterparty class is exempt from the velocity tax rate. Any exemption \u2014 permanent, temporary, or conditional \u2014 requires the same two-thirds supermajority in both chambers as the threshold floor (Safeguard 2), plus a mandatory CBO analysis showing the distributional impact of the exemption on households below median income, published in full before the vote. \u2018Systemic liquidity risk\u2019 is not a statutory basis for exemption \u2014 it is the argument every exemption request will make. If the argument were sufficient, the circuit breaker mechanism (Mode 3) is the correct response: a universal rate ceiling applied to all transactions equally, not a carve-out for preferred instruments. Allied legislators must treat any exemption request as a structural attack on the instrument, regardless of the justification offered."
      ),

      sp(200),

      // Section IV
      new Paragraph({children:[new PageBreak()]}),
      h1("IV. Red Lines in Legislative Negotiation"),
      body("The following table identifies the pressure points where the financial sector and its legislative allies will focus their negotiating effort. Each item describes what they will propose and what protection must be maintained."),
      sp(120),

      new Table({
        width:{size:9720,type:WidthType.DXA},
        columnWidths:[3480,6240],
        rows:[
          new TableRow({children:[
            new TableCell({borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},
              margins:{top:80,bottom:80,left:120,right:120},width:{size:3480,type:WidthType.DXA},
              children:[new Paragraph({children:[new TextRun({text:"PRESSURE POINT",color:WHITE,bold:true,size:20,font:"Arial"})]})] }),
            new TableCell({borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},
              margins:{top:80,bottom:80,left:120,right:120},width:{size:6240,type:WidthType.DXA},
              children:[new Paragraph({children:[new TextRun({text:"WHAT TO PROTECT",color:WHITE,bold:true,size:20,font:"Arial"})]})] }),
          ]}),
          redlineRow(
            "\"Pilot only\" framing",
            "The pilot's revenue allocation structure must be identical to the permanent program's. A pilot that funds debt paydown while the permanent program funds social programs creates no precedent and no constituency."
          ),
          redlineRow(
            "\"Revenue neutral\" requirement",
            "Velocity taxation is explicitly NOT revenue neutral. It generates surplus. Demanding revenue neutrality as a condition forces offsetting tax cuts that benefit the wealthy and eliminate the social dividend. Reject this condition entirely."
          ),
          redlineRow(
            "Bipartisan commission to \"study\" allocation",
            "The revenue allocation must be in the bill, not delegated to a commission. Commissions delay, and delay is the mechanism through which social programs get decoupled from the instrument."
          ),
          redlineRow(
            "Financial industry carve-outs",
            "Any transaction exemption for a specific instrument or sector \u2014 derivatives, repo markets, currency swaps, interbank lending \u2014 is a carve-out. Each carve-out reduces the base and requires raising rates on what remains, which shifts burden toward smaller participants. Reject all sector-specific exemptions."
          ),
          redlineRow(
            "\"Phase in\" social programs over 5 years",
            "Social programs must begin from the first dollar of revenue in the first month of the pilot. A phase-in structure allows the argument that the social dividend is \u2018not yet operational\u2019 to be used to justify sunset of the entire instrument before benefits accrue to the working population."
          ),
          redlineRow(
            "IRS enforcement retained",
            "The velocity tax is self-collecting at the clearing layer. There is no returns-based enforcement function. Retaining IRS enforcement infrastructure for the velocity tax is the mechanism through which audit-based avoidance strategies are later permitted. The transformation of the IRS from enforcement to economic development must be concurrent with implementation, not deferred."
          ),
          redlineRow(
            "Financial sector carve-out requests of any kind",
            "The political answer is simple and must be stated publicly: the federal government\u2019s own transactions are subject to this rate. State and local government transactions are subject to this rate. No public entity \u2014 Congress, the Pentagon, the Treasury \u2014 receives an exemption. When the financial sector requests a carve-out, the answer on the floor is: explain why you deserve a privilege that the United States government itself does not receive. This framing makes a carve-out vote politically toxic. Use it."
          ),
          redlineRow(
            "\u2018Rebate instead of rate reduction\u2019 as carve-out substitute",
            "The conditional rebate is open to any entity that remits velocity tax \u2014 HFT firms, hedge funds, manufacturers, agricultural companies, regional banks, or any other participant. They pay the full rate. They get 5\u201310% back if they deploy into qualifying productive investment through a designated separate account with independent certification and full audit trail. Criminal liability for misuse applies to every rebate recipient without exception \u2014 there is no entity category that escapes the liability clause. This is not a carve-out. It is a productive investment incentive with real teeth. If any entity asks for a rebate without the productive investment condition and without the liability clause, that is a carve-out. Reject it."
          ),
        ]
      }),

      sp(200),

      // Section V
      new Paragraph({children:[new PageBreak()]}),
      h1("V. The Coalition Architecture"),
      body("Understanding who benefits and who opposes is essential for protecting the proposal through the legislative process. The opposing coalition is well-organized and well-funded. The supporting coalition is larger but requires activation."),
      sp(120),

      h2("Who Benefits (The Supporting Coalition)"),
      bullet("Working population: universal healthcare, guaranteed income, pensions \u2014 the largest existing political majority if activated"),
      bullet("Small and medium businesses: employer healthcare overhead eliminated entirely; workers with income security accept more flexible employment arrangements; a $7,000\u20138,000 per employee annual cost reduction that exceeds any transaction friction on productive commerce"),
      bullet("Domestic manufacturers and productive investors: conditional rebate mechanism returns a fraction of remitted tax conditioned on investment in tangible productive assets; the instrument explicitly favors production over speculation"),
      bullet("Retirees: universal pensions eliminate the retirement security anxiety that shapes electoral behavior more than any other single factor"),
      bullet("Entrepreneurs and startups: workers who have healthcare and income security take job risks \u2014 entrepreneurship requires the freedom to fail without catastrophic personal consequences"),
      bullet("Rural districts: district-based revenue deployment through the transformed IRS network means agricultural infrastructure, rural broadband, water systems \u2014 exactly the capital rural districts cannot attract through private markets"),
      sp(120),

      h2("Who Opposes (The Blocking Coalition)"),
      bullet("High-frequency trading firms: the instrument is specifically most burdensome on maximum-volume speculative transactions; this constituency has very high political spending and very low popular sympathy"),
      bullet("Tax avoidance industry: the velocity tax has no returns and no complexity; the entire industry of tax attorneys, accountants, and avoidance-structure designers becomes unnecessary; their business model depends on income-based tax complexity"),
      bullet("Wealth management and private equity: capital gains tax elimination sounds attractive but comes with velocity friction on portfolio churn; the instrument rewards holding over trading"),
      bullet("Financial sector broadly: the velocity tax applies friction to the sector that generates the highest transaction volume; the industry will argue capital flight and systemic risk regardless of evidence"),
      sp(120),

      pullquote("The blocking coalition has concentrated financial power. The supporting coalition has distributed democratic power. This is the fundamental political structure. The instrument wins if the supporting coalition is activated before the blocking coalition captures implementation."),

      sp(200),

      // Section VI
      new Paragraph({children:[new PageBreak()]}),
      h1("VI. Sequencing Recommendation"),
      body("The following sequence is designed to build the supporting coalition before the blocking coalition can organize against the full instrument."),
      sp(80),

      numbered("ACTION 1-3 (Immediate): Treasury velocity study + Fed reporting mandate + de-dollarization dashboard. These are executive-authority actions that establish the data infrastructure. No legislation required. Creates institutional knowledge base and makes the problem visible in official records before the legislative fight begins."),
      sp(60),
      numbered("ACTION 4 (30 Days): Velocity Tax Pilot Act \u2014 0.1% on equity trades above $100,000. This is the politically viable entry point: it only touches financial transactions above consumer thresholds. Social program allocation must be in the bill from day one, even if the revenue is modest in the pilot stage. Establishes the precedent that social programs are the primary allocation."),
      sp(60),
      numbered("CRITICAL: The pilot bill must include the social program allocation structure in full, not as a placeholder. If the structure is absent in the pilot, it will not be inserted in the permanent program."),
      sp(60),
      numbered("ACTIONS 5-6 (30-90 Days): Conditional Rebate Design Commission + Dollar Reserve Protection Board. These build the productive-investment channel and the de-dollarization monitoring infrastructure simultaneously. Both generate institutional allies in the supporting coalition."),
      sp(60),
      numbered("ACTION 7 (90 Days): AI Monetary Management Authorization Act. This is the technically complex element and politically the most vulnerable to \"black box\" objections. It requires the data infrastructure from Actions 1-3 to be operational before it can be credibly proposed. The oversight provisions \u2014 congressional override, parameter transparency, financial sector exclusion \u2014 must be in the enabling legislation."),
      sp(60),
      numbered("ACTIONS 8-9 (Concurrent): Non-Dollar Clearing Protection + Intergenerational Fiscal Review Act. These are the defensive architecture: preventing resource warfare from creating permanent de-dollarization infrastructure, and constitutionally grounding the long-horizon obligation."),
      sp(60),
      numbered("ACTION 10 (Concurrent with 7): Seventh Generation Monetary Oversight Commission. Must be established before the AI system is operational. The Commission\u2019s authority to preemptively suspend AI rate adjustment must exist before the system it is overseeing is running."),

      sp(200),

      // Closing
      new Table({
        width:{size:9720,type:WidthType.DXA},columnWidths:[9720],
        rows:[new TableRow({children:[new TableCell({
          borders:cb(NAVY),shading:{fill:NAVY,type:ShadingType.CLEAR},
          margins:{top:240,bottom:240,left:480,right:480},
          width:{size:9720,type:WidthType.DXA},
          children:[
            new Paragraph({alignment:AlignmentType.CENTER,children:[
              new TextRun({text:"THE CORE PRINCIPLE TO HOLD",color:GOLD,bold:true,size:22,font:"Arial"})
            ]}),
            new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:120},children:[
              new TextRun({text:"Without the social dividend, this is a regressive tax.",color:WHITE,bold:true,size:26,font:"Arial"})
            ]}),
            new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80},children:[
              new TextRun({text:"With the social dividend, it is the most progressive fiscal reform in American history.",color:WHITE,size:24,font:"Arial"})
            ]}),
            new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:100},children:[
              new TextRun({text:"The social dividend is not the incentive offered to get the tax passed. It is the reason the tax exists. Any negotiation that treats them as separable is not a negotiation over terms. It is the capture of the instrument.",color:"FFD700",size:20,font:"Arial",italics:true})
            ]}),
          ]
        })]})],
      }),

    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("reports/allied_memo_2026-04-05.docx", buffer);
  console.log("Written: reports/allied_memo_2026-04-05.docx");
});
