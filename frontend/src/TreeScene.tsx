import React, { useEffect, useState } from 'react';
import { ArrowUpRight, Leaf } from 'lucide-react';

const notes = [
  { eyebrow: 'A SAFER SEARCH', title: 'Check the vacancy date.', copy: 'A fresh date is useful. Confirm the role on the employer’s own official channel before sharing details.', source: 'National Career Service', href: 'https://www.ncs.gov.in/', spot: 'note-left-high' },
  { eyebrow: 'SKILL OF THE DAY', title: 'Keep one project note.', copy: 'Write down what you built, which tools you used, and what you learned. That makes your skills easier to explain.', source: 'Career practice', href: '', spot: 'note-right-mid' },
  { eyebrow: 'PUBLIC SKILLS UPDATE', title: 'New technology skills are growing.', copy: 'A Ministry update described 50 emerging-technology qualifications on Skill India Digital Hub. Published 12 Aug 2026.', source: 'Press Information Bureau', href: 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2298226&lang=1&reg=1', spot: 'note-left-low' },
  { eyebrow: 'A SIMPLE SAFETY RULE', title: 'Never pay to get hired.', copy: 'Application, interview, training-kit, and placement fees are warning signs. Stop and verify independently.', source: 'National Career Service', href: 'https://www.ncs.gov.in/', spot: 'note-right-high' },
];

export default function TreeScene() {
  const [active, setActive] = useState(0);
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const timer = window.setInterval(() => setActive((index) => (index + 1) % notes.length), 5000);
    return () => window.clearInterval(timer);
  }, []);
  const note = notes[active];
  return <figure className="tree-scene" aria-label="A banyan tree connecting safer opportunities and career guidance">
    <img className="tree-art" src="/images/banyan-tree-hero.jpg" alt="A mature banyan tree with a broad canopy, hanging roots, and roots spreading across the ground" fetchPriority="high" />
    <span className="falling-leaf leaf-one" aria-hidden="true" />
    <span className="falling-leaf leaf-two" aria-hidden="true" />
    <span className="falling-leaf leaf-three" aria-hidden="true" />
    <span className="falling-leaf leaf-four" aria-hidden="true" />
    <span className={`note-leaf ${note.spot}`} aria-hidden="true"><Leaf size={16}/></span>
    <div className={`leaf-note ${note.spot}`} key={active} role="note" aria-live="polite" aria-atomic="true">
      <div className="leaf-note-eyebrow"><span/> {note.eyebrow}</div>
      <b>{note.title}</b>
      <p>{note.copy}</p>
      <div className="leaf-note-footer"><span>{note.source}</span>{note.href&&<a href={note.href} target="_blank" rel="noreferrer" aria-label={`Read source: ${note.source}`}><ArrowUpRight size={14}/></a>}</div>
    </div>
    <div className="leaf-note-pagination" aria-label={`Career note ${active+1} of ${notes.length}`}>
      {notes.map((item,index)=><button key={item.eyebrow} type="button" aria-label={`Show note ${index+1}: ${item.eyebrow}`} aria-current={index===active?'step':undefined} onClick={()=>setActive(index)}/>) }
      <span>New note every 5 seconds</span>
    </div>
    <figcaption className="tree-caption"><span className="tree-caption-dot"/>Good roots. Safer connections. Room to grow.</figcaption>
  </figure>;
}
