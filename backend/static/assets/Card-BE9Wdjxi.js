import{r as t,j as s,k as o}from"./index-COpFP_51.js";/**
 * @license lucide-react v0.460.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x=r=>r.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase(),i=(...r)=>r.filter((e,a,d)=>!!e&&e.trim()!==""&&d.indexOf(e)===a).join(" ").trim();/**
 * @license lucide-react v0.460.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var u={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:2,strokeLinecap:"round",strokeLinejoin:"round"};/**
 * @license lucide-react v0.460.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g=t.forwardRef(({color:r="currentColor",size:e=24,strokeWidth:a=2,absoluteStrokeWidth:d,className:c="",children:n,iconNode:l,...m},f)=>t.createElement("svg",{ref:f,...u,width:e,height:e,stroke:r,strokeWidth:d?Number(a)*24/Number(e):a,className:i("lucide",c),...m},[...l.map(([p,C])=>t.createElement(p,C)),...Array.isArray(n)?n:[n]]));/**
 * @license lucide-react v0.460.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w=(r,e)=>{const a=t.forwardRef(({className:d,...c},n)=>t.createElement(g,{ref:n,iconNode:e,className:i(`lucide-${x(r)}`,d),...c}));return a.displayName=`${r}`,a};/**
 * @license lucide-react v0.460.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const v=w("CircleCheckBig",[["path",{d:"M21.801 10A10 10 0 1 1 17 3.335",key:"yps3ct"}],["path",{d:"m9 11 3 3L22 4",key:"1pflzl"}]]),N=t.forwardRef(({className:r,...e},a)=>s.jsx("div",{ref:a,className:o("rounded-lg border bg-card text-card-foreground shadow-sm",r),...e}));N.displayName="Card";const h=t.forwardRef(({className:r,...e},a)=>s.jsx("div",{ref:a,className:o("flex flex-col space-y-1.5 p-6",r),...e}));h.displayName="CardHeader";const y=t.forwardRef(({className:r,...e},a)=>s.jsx("h3",{ref:a,className:o("text-2xl font-semibold leading-none tracking-tight",r),...e}));y.displayName="CardTitle";const k=t.forwardRef(({className:r,...e},a)=>s.jsx("p",{ref:a,className:o("text-sm text-muted-foreground",r),...e}));k.displayName="CardDescription";const j=t.forwardRef(({className:r,...e},a)=>s.jsx("div",{ref:a,className:o("p-6 pt-0",r),...e}));j.displayName="CardContent";const b=t.forwardRef(({className:r,...e},a)=>s.jsx("div",{ref:a,className:o("flex items-center p-6 pt-0",r),...e}));b.displayName="CardFooter";export{N as C,j as a,h as b,w as c,y as d,v as e,k as f,b as g};
