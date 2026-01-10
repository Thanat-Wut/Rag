import FadeInUp from '../magic/FadeInUp';

export default function Page2_Solution() {
  return (
    <div className="bg-white text-slate-900 w-full h-full flex flex-col items-center justify-center p-8 relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-orange-100 rounded-full blur-3xl opacity-50 translate-x-1/2 -translate-y-1/2"></div>

      <FadeInUp>
        <div className="text-center mb-12">
          <span className="text-orange-600 font-bold tracking-wider uppercase mb-2 block">Our Solution</span>
          <h2 className="text-4xl md:text-6xl font-bold mb-6">WUT Internal Helpdesk</h2>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto">
            ระบบ "สมองกลาง" (AI Orchestrator) ที่ช่วยแยกแยะ ตัดสินใจ และหาคำตอบให้พนักงานอัตโนมัติ
          </p>
        </div>
      </FadeInUp>

      <div className="relative w-full max-w-5xl">
        {/* Simple Flow Diagram */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 mt-8">
          <Card step="1" title="User Ask" icon="🙋‍♂️" desc="รับคำถามผ่าน Chat" />
          <Arrow />
          <Card step="2" title="Classify" icon="🧠" desc="แยกแผนก (IT/HR/Acc)" highlight />
          <Arrow />
          <Card step="3" title="Decision" icon="⚖️" desc="ตอบเอง หรือ ส่งต่อ?" />
          <Arrow />
          <Card step="4" title="Action" icon="⚡" desc="ตอบทันที / สร้าง Ticket" />
        </div>
      </div>
    </div>
  );
}

function Card({ step, title, icon, desc, highlight = false }: any) {
  return (
    <div className={`p-6 rounded-xl border-2 w-full md:w-64 text-center transition-all hover:-translate-y-2 shadow-lg ${highlight ? 'border-orange-500 bg-orange-50' : 'border-slate-100 bg-white'}`}>
      <div className="text-sm font-bold text-slate-400 mb-2">STEP {step}</div>
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="text-xl font-bold mb-1">{title}</h3>
      <p className="text-sm text-slate-500">{desc}</p>
    </div>
  );
}

function Arrow() {
  return <div className="hidden md:block text-slate-300 text-3xl">➔</div>;
}