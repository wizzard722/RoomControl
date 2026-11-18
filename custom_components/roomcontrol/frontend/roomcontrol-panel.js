var e=globalThis,t=e.ShadowRoot&&(e.ShadyCSS===void 0||e.ShadyCSS.nativeShadow)&&`adoptedStyleSheets`in Document.prototype&&`replace`in CSSStyleSheet.prototype,n=Symbol(),r=new WeakMap,i=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==n)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,n=this.t;if(t&&e===void 0){let t=n!==void 0&&n.length===1;t&&(e=r.get(n)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&r.set(n,e))}return e}toString(){return this.cssText}},a=e=>new i(typeof e==`string`?e:e+``,void 0,n),o=(e,...t)=>new i(e.length===1?e[0]:t.reduce((t,n,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if(typeof e==`number`)return e;throw Error(`Value passed to 'css' function must be a 'css' function result: `+e+`. Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.`)})(n)+e[r+1],e[0]),e,n),s=(n,r)=>{if(t)n.adoptedStyleSheets=r.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let t of r){let r=document.createElement(`style`),i=e.litNonce;i!==void 0&&r.setAttribute(`nonce`,i),r.textContent=t.cssText,n.appendChild(r)}},c=t?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t=``;for(let n of e.cssRules)t+=n.cssText;return a(t)})(e):e,{is:l,defineProperty:u,getOwnPropertyDescriptor:d,getOwnPropertyNames:f,getOwnPropertySymbols:p,getPrototypeOf:m}=Object,h=globalThis,g=h.trustedTypes,_=g?g.emptyScript:``,v=h.reactiveElementPolyfillSupport,y=(e,t)=>e,b={toAttribute(e,t){switch(t){case Boolean:e=e?_:null;break;case Object:case Array:e=e==null?e:JSON.stringify(e)}return e},fromAttribute(e,t){let n=e;switch(t){case Boolean:n=e!==null;break;case Number:n=e===null?null:Number(e);break;case Object:case Array:try{n=JSON.parse(e)}catch{n=null}}return n}},x=(e,t)=>!l(e,t),S={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:x};Symbol.metadata??=Symbol(`metadata`),h.litPropertyMetadata??=new WeakMap;var C=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=S){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let n=Symbol(),r=this.getPropertyDescriptor(e,n,t);r!==void 0&&u(this.prototype,e,r)}}static getPropertyDescriptor(e,t,n){let{get:r,set:i}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){let a=r?.call(this);i?.call(this,t),this.requestUpdate(e,a,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??S}static _$Ei(){if(this.hasOwnProperty(y(`elementProperties`)))return;let e=m(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(y(`finalized`)))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(y(`properties`))){let e=this.properties,t=[...f(e),...p(e)];for(let n of t)this.createProperty(n,e[n])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[e,n]of t)this.elementProperties.set(e,n)}this._$Eh=new Map;for(let[e,t]of this.elementProperties){let n=this._$Eu(e,t);n!==void 0&&this._$Eh.set(n,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let n=new Set(e.flat(1/0).reverse());for(let e of n)t.unshift(c(e))}else e!==void 0&&t.push(c(e));return t}static _$Eu(e,t){let n=t.attribute;return!1===n?void 0:typeof n==`string`?n:typeof e==`string`?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let n of t.keys())this.hasOwnProperty(n)&&(e.set(n,this[n]),delete this[n]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return s(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,n){this._$AK(e,n)}_$ET(e,t){let n=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,n);if(r!==void 0&&!0===n.reflect){let i=(n.converter?.toAttribute===void 0?b:n.converter).toAttribute(t,n.type);this._$Em=e,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(e,t){let n=this.constructor,r=n._$Eh.get(e);if(r!==void 0&&this._$Em!==r){let e=n.getPropertyOptions(r),i=typeof e.converter==`function`?{fromAttribute:e.converter}:e.converter?.fromAttribute===void 0?b:e.converter;this._$Em=r;let a=i.fromAttribute(t,e.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(e,t,n,r=!1,i){if(e!==void 0){let a=this.constructor;if(!1===r&&(i=this[e]),n??=a.getPropertyOptions(e),!((n.hasChanged??x)(i,t)||n.useDefault&&n.reflect&&i===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,n))))return;this.C(e,t,n)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:n,reflect:r,wrapped:i},a){n&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),!0!==i||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||n||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[t,n]of e){let{wrapped:e}=n,r=this[t];!0!==e||this._$AL.has(t)||r===void 0||this.C(t,void 0,n,r)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};C.elementStyles=[],C.shadowRootOptions={mode:`open`},C[y(`elementProperties`)]=new Map,C[y(`finalized`)]=new Map,v?.({ReactiveElement:C}),(h.reactiveElementVersions??=[]).push(`2.1.2`);var ee=globalThis,w=e=>e,T=ee.trustedTypes,te=T?T.createPolicy(`lit-html`,{createHTML:e=>e}):void 0,E=`$lit$`,D=`lit$${Math.random().toFixed(9).slice(2)}$`,O=`?`+D,k=`<${O}>`,A=document,ne=()=>A.createComment(``),j=e=>e===null||typeof e!=`object`&&typeof e!=`function`,M=Array.isArray,re=e=>M(e)||typeof e?.[Symbol.iterator]==`function`,ie=`[ 	
\f\r]`,ae=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,N=/-->/g,oe=/>/g,P=RegExp(`>|${ie}(?:([^\\s"'>=/]+)(${ie}*=${ie}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,`g`),se=/'/g,ce=/"/g,le=/^(?:script|style|textarea|title)$/i,ue=e=>(t,...n)=>({_$litType$:e,strings:t,values:n}),F=ue(1),I=ue(2),de=Symbol.for(`lit-noChange`),L=Symbol.for(`lit-nothing`),fe=new WeakMap,pe=A.createTreeWalker(A,129);function me(e,t){if(!M(e)||!e.hasOwnProperty(`raw`))throw Error(`invalid template strings array`);return te===void 0?t:te.createHTML(t)}var he=(e,t)=>{let n=e.length-1,r=[],i,a=t===2?`<svg>`:t===3?`<math>`:``,o=ae;for(let t=0;t<n;t++){let n=e[t],s,c,l=-1,u=0;for(;u<n.length&&(o.lastIndex=u,c=o.exec(n),c!==null);)u=o.lastIndex,o===ae?c[1]===`!--`?o=N:c[1]===void 0?c[2]===void 0?c[3]!==void 0&&(o=P):(le.test(c[2])&&(i=RegExp(`</`+c[2],`g`)),o=P):o=oe:o===P?c[0]===`>`?(o=i??ae,l=-1):c[1]===void 0?l=-2:(l=o.lastIndex-c[2].length,s=c[1],o=c[3]===void 0?P:c[3]===`"`?ce:se):o===ce||o===se?o=P:o===N||o===oe?o=ae:(o=P,i=void 0);let d=o===P&&e[t+1].startsWith(`/>`)?` `:``;a+=o===ae?n+k:l>=0?(r.push(s),n.slice(0,l)+E+n.slice(l)+D+d):n+D+(l===-2?t:d)}return[me(e,a+(e[n]||`<?>`)+(t===2?`</svg>`:t===3?`</math>`:``)),r]},ge=class e{constructor({strings:t,_$litType$:n},r){let i;this.parts=[];let a=0,o=0,s=t.length-1,c=this.parts,[l,u]=he(t,n);if(this.el=e.createElement(l,r),pe.currentNode=this.el.content,n===2||n===3){let e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;(i=pe.nextNode())!==null&&c.length<s;){if(i.nodeType===1){if(i.hasAttributes())for(let e of i.getAttributeNames())if(e.endsWith(E)){let t=u[o++],n=i.getAttribute(e).split(D),r=/([.?@])?(.*)/.exec(t);c.push({type:1,index:a,name:r[2],strings:n,ctor:r[1]===`.`?xe:r[1]===`?`?Se:r[1]===`@`?Ce:be}),i.removeAttribute(e)}else e.startsWith(D)&&(c.push({type:6,index:a}),i.removeAttribute(e));if(le.test(i.tagName)){let e=i.textContent.split(D),t=e.length-1;if(t>0){i.textContent=T?T.emptyScript:``;for(let n=0;n<t;n++)i.append(e[n],ne()),pe.nextNode(),c.push({type:2,index:++a});i.append(e[t],ne())}}}else if(i.nodeType===8){if(i.data===O)c.push({type:2,index:a});else{let e=-1;for(;(e=i.data.indexOf(D,e+1))!==-1;)c.push({type:7,index:a}),e+=D.length-1}}a++}}static createElement(e,t){let n=A.createElement(`template`);return n.innerHTML=e,n}};function _e(e,t,n=e,r){if(t===de)return t;let i=r===void 0?n._$Cl:n._$Co?.[r],a=j(t)?void 0:t._$litDirective$;return i?.constructor!==a&&(i?._$AO?.(!1),a===void 0?i=void 0:(i=new a(e),i._$AT(e,n,r)),r===void 0?n._$Cl=i:(n._$Co??=[])[r]=i),i!==void 0&&(t=_e(e,i._$AS(e,t.values),i,r)),t}var ve=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:n}=this._$AD,r=(e?.creationScope??A).importNode(t,!0);pe.currentNode=r;let i=pe.nextNode(),a=0,o=0,s=n[0];for(;s!==void 0;){if(a===s.index){let t;s.type===2?t=new ye(i,i.nextSibling,this,e):s.type===1?t=new s.ctor(i,s.name,s.strings,this,e):s.type===6&&(t=new we(i,this,e)),this._$AV.push(t),s=n[++o]}a!==s?.index&&(i=pe.nextNode(),a++)}return pe.currentNode=A,r}p(e){let t=0;for(let n of this._$AV)n!==void 0&&(n.strings===void 0?n._$AI(e[t]):(n._$AI(e,n,t),t+=n.strings.length-2)),t++}},ye=class e{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,n,r){this.type=2,this._$AH=L,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=n,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=_e(this,e,t),j(e)?e===L||e==null||e===``?(this._$AH!==L&&this._$AR(),this._$AH=L):e!==this._$AH&&e!==de&&this._(e):e._$litType$===void 0?e.nodeType===void 0?re(e)?this.k(e):this._(e):this.T(e):this.$(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==L&&j(this._$AH)?this._$AA.nextSibling.data=e:this.T(A.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:n}=e,r=typeof n==`number`?this._$AC(e):(n.el===void 0&&(n.el=ge.createElement(me(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===r)this._$AH.p(t);else{let e=new ve(r,this),n=e.u(this.options);e.p(t),this.T(n),this._$AH=e}}_$AC(e){let t=fe.get(e.strings);return t===void 0&&fe.set(e.strings,t=new ge(e)),t}k(t){M(this._$AH)||(this._$AH=[],this._$AR());let n=this._$AH,r,i=0;for(let a of t)i===n.length?n.push(r=new e(this.O(ne()),this.O(ne()),this,this.options)):r=n[i],r._$AI(a),i++;i<n.length&&(this._$AR(r&&r._$AB.nextSibling,i),n.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let t=w(e).nextSibling;w(e).remove(),e=t}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},be=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,n,r,i){this.type=1,this._$AH=L,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=i,n.length>2||n[0]!==``||n[1]!==``?(this._$AH=Array(n.length-1).fill(new String),this.strings=n):this._$AH=L}_$AI(e,t=this,n,r){let i=this.strings,a=!1;if(i===void 0)e=_e(this,e,t,0),a=!j(e)||e!==this._$AH&&e!==de,a&&(this._$AH=e);else{let r=e,o,s;for(e=i[0],o=0;o<i.length-1;o++)s=_e(this,r[n+o],t,o),s===de&&(s=this._$AH[o]),a||=!j(s)||s!==this._$AH[o],s===L?e=L:e!==L&&(e+=(s??``)+i[o+1]),this._$AH[o]=s}a&&!r&&this.j(e)}j(e){e===L?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??``)}},xe=class extends be{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===L?void 0:e}},Se=class extends be{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==L)}},Ce=class extends be{constructor(e,t,n,r,i){super(e,t,n,r,i),this.type=5}_$AI(e,t=this){if((e=_e(this,e,t,0)??L)===de)return;let n=this._$AH,r=e===L&&n!==L||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,i=e!==L&&(n===L||r);r&&this.element.removeEventListener(this.name,this,n),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH==`function`?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},we=class{constructor(e,t,n){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(e){_e(this,e)}},Te=ee.litHtmlPolyfillSupport;Te?.(ge,ye),(ee.litHtmlVersions??=[]).push(`3.3.3`);var Ee=(e,t,n)=>{let r=n?.renderBefore??t,i=r._$litPart$;if(i===void 0){let e=n?.renderBefore??null;r._$litPart$=i=new ye(t.insertBefore(ne(),e),e,void 0,n??{})}return i._$AI(e),i},De=globalThis,R=class extends C{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=Ee(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return de}};R._$litElement$=!0,R.finalized=!0,De.litElementHydrateSupport?.({LitElement:R});var Oe=De.litElementPolyfillSupport;Oe?.({LitElement:R}),(De.litElementVersions??=[]).push(`4.2.2`);var ke=e=>(t,n)=>{n===void 0?customElements.define(e,t):n.addInitializer(()=>{customElements.define(e,t)})},Ae={attribute:!0,type:String,converter:b,reflect:!1,hasChanged:x},je=(e=Ae,t,n)=>{let{kind:r,metadata:i}=n,a=globalThis.litPropertyMetadata.get(i);if(a===void 0&&globalThis.litPropertyMetadata.set(i,a=new Map),r===`setter`&&((e=Object.create(e)).wrapped=!0),a.set(n.name,e),r===`accessor`){let{name:r}=n;return{set(n){let i=t.get.call(this);t.set.call(this,n),this.requestUpdate(r,i,e,!0,n)},init(t){return t!==void 0&&this.C(r,void 0,e,t),t}}}if(r===`setter`){let{name:r}=n;return function(n){let i=this[r];t.call(this,n),this.requestUpdate(r,i,e,!0,n)}}throw Error(`Unsupported decorator location: `+r)};function z(e){return(t,n)=>typeof n==`object`?je(e,t,n):((e,t,n)=>{let r=t.hasOwnProperty(n);return t.constructor.createProperty(n,e),r?Object.getOwnPropertyDescriptor(t,n):void 0})(e,t,n)}function B(e){return z({...e,state:!0,attribute:!1})}var Me=o`
  :host {
    --vr-radius: var(--ha-card-border-radius, 12px);
    --vr-radius-sm: 8px;
    --vr-fill: color-mix(in srgb, var(--secondary-text-color) 8%, transparent);
    --vr-fill-strong: color-mix(in srgb, var(--secondary-text-color) 14%, transparent);
    --vr-fill-primary: color-mix(in srgb, var(--primary-color) 10%, transparent);
    --vr-on: var(--warning-color, #f59e0b);
    --vr-on-bg: color-mix(in srgb, var(--vr-on) 12%, transparent);
    --vr-off: var(--secondary-text-color);
    --vr-motion: var(--info-color, #3b82f6);
    --vr-home: color-mix(in srgb, var(--success-color, #43a047) 70%, white);
    --vr-home-bg: color-mix(in srgb, var(--success-color, #43a047) 22%, transparent);
    --vr-dusk: color-mix(in srgb, #6366f1 60%, var(--primary-text-color));
    --vr-border: var(--divider-color);
    --vr-border-strong: color-mix(in srgb, var(--primary-text-color) 22%, transparent);
    --vr-surface: var(--card-background-color, var(--ha-card-background));
    --vr-shadow-pop: 0 1px 3px rgb(0 0 0 / 12%), 0 8px 24px rgb(0 0 0 / 22%);
    --vr-space-1: 4px;
    --vr-space-2: 8px;
    --vr-space-3: 12px;
    --vr-space-4: 16px;
    --vr-space-5: 20px;
    --vr-space-6: 24px;
    --vr-font-xs: 11px;
    --vr-font-sm: 12px;
    --vr-font-md: 14px;
    --vr-font-lg: 16px;
    --vr-font-xl: 20px;
    --vr-touch: 44px;
  }
`;o`
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
  }
`;var Ne={en:{"panel.title":`RoomControl`,"panel.version":`RoomControl version`,"panel.loading":`Loading…`,"panel.load_error":`Could not load room configuration.`,"panel.no_rooms":`No areas found.`,"panel.no_rooms_hint":`Create areas in Settings → Areas, labels & zones.`,"room.back":`Back`,"room.lights_section":`Lights`,"room.lights_add":`Add light`,"room.lights_none":`No lights assigned`,"room.motion_section":`Motion sensor`,"room.motion_none":`No motion sensors`,"room.motion_pick":`Pick a motion sensor`,"room.dusk_section":`On when it gets dark`,"room.dusk_hint":`Turns the lights on at the moment it gets dark (the sun sets). Lights switched on then stay on outside the schedule until it is light again.`,"room.save":`Save`,"room.saving":`Saving…`,"room.saved":`Saved`,"room.error_save":`Could not save`,"card.on":`On`,"card.off":`Off`,"card.motion":`Motion`,"card.dusk":`Dark`,"card.lights":`light`,"card.lights_plural":`lights`,"room.lux_section":`Lux sensors`,"room.lux_pick":`Pick a lux / illuminance sensor`,"room.target_lux":`Target illuminance (lux)`,"room.lux_hint":`Dims or brightens lights to reach the target lux.`,"room.lux_now":`Current`,"room.lux_target":`Target`,"settings.title":`Settings`,"common.close":`Close`,"common.remove":`Remove`,"common.retry":`Retry`,"room.motion_clear":`Clear`,"room.lux_none":`No lux sensor`,"room.sensor_add":`Add sensor`,"room.area_no_lights":`No other lights in this area. Assign lights to the area in Home Assistant first.`,"room.area_no_motion":`No motion sensors in this area. Assign one to the area in Home Assistant first.`,"room.area_no_lux":`No lux sensors in this area. Assign one to the area in Home Assistant first.`,"room.alarm_section":`Alarm`,"room.alarm_pick":`Pick an alarm panel`,"room.alarm_none":`No alarm panels found in Home Assistant.`,"card.outside_schedule":`Outside schedule`,"room.schedules_section":`Schedules`,"room.schedules_add":`Add schedule`,"room.schedules_none":`No schedules: lights may be on at any time.`,"room.schedules_pick":`Pick a schedule`,"room.schedules_none_in_ha":`No schedules in Home Assistant. Create one in Settings → Devices & services → Helpers → Schedule.`,"room.schedule_active":`active`,"room.schedule_word":`schedule`,"room.schedule_no_limit":`no limit`,"room.selector_section":`Active schedule chosen by`,"room.selector_pick":`Pick an input_number`,"room.selector_none_in_ha":`No input_number helpers in Home Assistant.`,"room.selector_hint":`Value 1 = first schedule, 2 = second, and so on. 0 = no limit. During the active schedule the bundles that follow it go on when it is dark. Outside the schedule only motion turns the lights on, off after the grace period without motion.`,"room.lights_select_all":`Select all`,"room.lights_add_selected":`Add`,"common.cancel":`Cancel`,"panel.hidden_rooms":`Hidden`,"panel.all_hidden":`All rooms are hidden.`,"card.hide":`Hide`,"card.unhide":`Show`,"room.tab_settings":`Settings`,"room.tab_analysis":`Analysis`,"analysis.period":`Period`,"analysis.period_24h":`24 hours`,"analysis.period_7d":`7 days`,"analysis.period_30d":`30 days`,"analysis.retention_note":`Home Assistant keeps 10 days of history by default (recorder purge_keep_days); older days show as 0.`,"analysis.no_lights":`Add lights to this room to see its usage.`,"analysis.load_error":`Could not load the history.`,"analysis.hour_short":`h`,"analysis.on_time":`Hours on`,"analysis.switched_on":`Times switched on`,"analysis.avg_per_day":`Average per day`,"analysis.on_without_motion":`On without motion`,"analysis.detections":`detections`,"analysis.no_motion_sensor":`No motion sensor configured`,"analysis.chart_per_day":`Hours on per day`,"analysis.chart_per_hour":`Minutes on per hour`,"analysis.chart_profile":`When the lights are on (average minutes per hour of the day)`,"analysis.minutes_on":`Minutes on`,"analysis.avg_minutes_on":`Avg. minutes on`,"analysis.show_table":`Show as table`,"analysis.per_lamp":`Per lamp`,"analysis.lamp":`Lamp`,"status.active":`Active`,"status.standby":`Standby`,"overview.title":`Overview`,"person.home":`Home`,"person.away":`Away`,"card.nobody_home":`Nobody home`,"settings.presence":`Presence`,"settings.presence_hint":`Choose the people RoomControl follows. In each room you link one or more of them: lights there only work while one of them is home, and go off when the last one leaves.`,"settings.no_persons":`No persons in Home Assistant.`,"settings.display":`Display`,"settings.group_by_floor":`Group rooms by floor`,"settings.group_by_floor_hint":`Uses the floors from Home Assistant (Settings → Areas, labels & zones).`,"settings.no_floors":`No floors in Home Assistant yet. Add them in Settings → Areas, labels & zones.`,"floors.none":`No floor`,"room.presence_section":`Presence`,"room.presence_no_persons":`Choose people in RoomControl's settings (gear icon on the dashboard) first.`,"room.presence_hint":`With people linked, lights only work while one of them is home and go off when the last one leaves. With nobody linked, presence is ignored.`,"room.daylight_section":`Follow outdoor light`,"room.daylight_title":`Colour follows the sun`,"room.daylight_hint":`Warm white when the sun is low or down, cooler when it is high. Only the lamps you tick below.`,"room.daylight_now":`Now`,"dim.to_1":`Switch Dim on`,"dim.restore":`Back to previous brightness`,"dim.all_to_1":`Switch Dim on in all configured rooms`,"dim.restore_all":`Restore brightness in all rooms`,"dim.all_short":`All dim`,"dim.restore_all_short":`All back`,"dim.error":`Could not dim the lights.`,"room.motion_multi_hint":`Lights go on when any sensor detects motion, and off only when all sensors have been clear for the grace period.`,"room.selector_required":`Required with more than one schedule: pick the input_number that chooses the active one.`,"room.links_section":`Linked rooms`,"room.links_add":`Link room`,"room.links_none":`Not linked to other rooms`,"room.links_none_available":`No other rooms to link.`,"room.links_hint":`Motion in any linked room turns the lights on here too; they go off once all motion sensors of all linked rooms have been clear for the grace period. Links work both ways.`,"room.links_group":`Together with`,"card.linked_with":`Linked with`,"room.daylight_lamps":`Lamps that follow the sun`,"room.daylight_not_capable":`No colour temperature`,"room.daylight_pick_required":`Pick at least one lamp; until then no lamp changes colour.`,"room.daylight_no_lights":`Add lights to this room first.`,"grace.label":`Grace period`,"grace.left":`left`,"grace.setting":`Lights stay on without motion`,"grace.immediately":`off as soon as motion stops`,"grace.setting_hint":`Max. 10 minutes. Applies to lights motion turned on, and to linked rooms.`,"grace.hint":`No motion; lights go off when the grace period ends`,"analysis.avg_brightness":`Avg. brightness`,"analysis.avg_lux":`Avg. light in room`,"analysis.while_on":`while the lights were on`,"analysis.no_lux_sensor":`No lux sensor configured`,"analysis.chart_brightness_day":`Brightness the lights burned at (average per day)`,"analysis.chart_brightness_hour":`Brightness the lights burned at (average per hour)`,"analysis.chart_lux_day":`Light in the room while the lights were on (average lux per day)`,"analysis.chart_lux_hour":`Light in the room while the lights were on (average lux per hour)`,"manual.title":`Manual control`,"full_control.title":`Full control by RoomControl`,"full_control.off_hint":`Off: lamps and curtains also respond to switches, other apps and automations.`,"full_control.on_hint":`On: lamps and curtains only follow RoomControl (automatic, this panel and the RoomControl entities). Any other change is put back. During manual control you can operate them yourself.`,"manual.short":`Manual`,"manual.start":`Take over`,"manual.stop":`Hand back`,"manual.active":`RoomControl does nothing in this room`,"manual.duration":`Duration of manual control`,"manual.hint":`RoomControl does nothing automatic here for the chosen time, then takes over again.`,"manual.error":`Could not change manual control.`,"analysis.today":`Today`,"analysis.now":`Now`,"health.restart":`The RoomControl backend running in Home Assistant ({running}) is older than this panel ({expected}). Restart Home Assistant (Settings → System → Restart) so the new version runs; until then motion, time slots and the other rules use the old code.`,"health.old":`older than 1.1.0`,"health.inactive":`RoomControl has no room lights, so nothing reacts to motion or time slots. Check that RoomControl is added under Settings → Devices & services and look for “roomcontrol” in the log.`,"motion_note.ignored":`Last motion ignored`,"motion_note.manual":`manual control is active`,"motion_note.no_lights":`this room has no lights`,"motion_note.already_on":`the lights were already on`,"motion_note.nobody_home":`nobody linked to this room is home`,"motion_note.slot":`a time slot is running: its bundles are on at their level`,"debug.wants_on_slot":`should be on (time slot running; it wins over motion)`,"motion_note.too_bright":`too bright ({lux} lx, target {target} lx)`,"motion_note.outside_window":`sensor outside its time window`,"motion_window.label":`Switches lights on from`,"motion_window.until":`to`,"motion_window.always":`always`,"motion_window.clear":`Always`,"motion_window.hint":`Outside this time window motion does not switch the lights on; lights that are already on stay on while there is motion. Empty = always. A window may run past midnight (e.g. 07:00 to 01:00).`,"motion_note.no_entity":`RoomControl has no light for this room yet, so motion does nothing here. Restart Home Assistant or check the RoomControl integration.`,"motion_note.not_tracked":`RoomControl is not following these sensors yet. Restart Home Assistant if you just updated RoomControl.`,"fixed.pin":`Pin to a fixed dim level (ignores the brightness slider and the lux sensor)`,"fixed.unpin":`Release fixed dim level`,"fixed.label":`Fixed level`,"fixed.slider_hint":`Pinned lamps keep their fixed level`,"groups.section":`Groups`,"groups.add":`New group`,"groups.none":`No groups yet. Each group becomes its own light on the room's device in Home Assistant (for dashboards); a lamp can be in more than one group.`,"groups.no_lights":`Add lights to this room first.`,"groups.default_name":`Group`,"groups.name":`Group name`,"groups.empty":`No lamps in this group`,"groups.brightness":`Brightness`,"groups.edit_lamps":`Change lamps`,"groups.pick_lamps":`Lamps in this group`,"door.section":`Door sensors`,"door.none":`No door sensors`,"door.none_in_area":`No door sensors in this area. Assign one to the area in Home Assistant first.`,"door.open":`Open`,"door.closed":`Closed`,"door.turn_on_title":`Lights on when a door opens`,"door.turn_on_hint_lux":`Only when the room is darker than the lux target ({target} lx). Without further motion they go off after the grace period.`,"door.turn_on_hint_nolux":`Without a lux target this always counts as dark enough. Without further motion they go off after the grace period.`,"door.groups":`Groups that go on`,"door.no_groups":`Create a lamp group in the Groups section first.`,"door.pick_group":`Pick at least one group; until then nothing goes on.`,"covers.section":`Curtains`,"covers.add":`Add curtain`,"covers.none":`No curtains`,"covers.none_in_area":`No curtains or blinds in this area. Assign them to the area in Home Assistant first.`,"covers.groups":`Curtain groups`,"covers.groups_none":`No groups yet. Group curtains to open and close them together, or let them follow dark/light.`,"covers.group_empty":`No curtains in this group`,"covers.open":`Open`,"covers.stop":`Stop`,"covers.close":`Close`,"covers.edit":`Change curtains`,"covers.pick":`Curtains in this group`,"covers.follow_title":`Follow dark/light`,"covers.follow_hint":`Close at dusk or dark, open at sunrise or a fixed time (see below). In between you can move them yourself.`,"covers.follow_hint_noschedule":`This room has no schedule: the curtains close when it gets dark and only open automatically with 'Open at'.`,"covers.state_open":`Open`,"covers.state_closed":`Closed`,"covers.state_opening":`Opening`,"covers.state_closing":`Closing`,"fan.section":`Fan`,"fan.add":`Add fan`,"fan.none":`No fan`,"fan.none_in_area":`No fans in this area. Assign one to the area in Home Assistant first.`,"fan.steps":`Speed by activity`,"fan.steps_none":`No steps yet: the fan is not controlled.`,"fan.after":`After`,"fan.minutes":`min`,"fan.speed":`Speed`,"fan.add_step":`Add step`,"fan.active_since":`Activity since`,"fan.idle":`No activity`,"fan.needs_motion":`Add a motion sensor to this room: activity is measured with motion.`,"fan.hint":`Activity starts at the first motion and lasts while there is motion, plus the run-on time. At each step the fan goes faster; when the activity ends, the fan goes off.`,"fan.temp_title":`On by temperature`,"fan.temp_off":`Off: the fan only goes on with activity.`,"fan.temp_hint":`From this temperature the fan runs, also without motion.`,"fan.temp_pick":`Choose a temperature sensor`,"fan.temp_none":`No temperature sensors in this room. Assign one to the area in Home Assistant first.`,"fan.temp_from":`From`,"fan.temp_active":`Now {temp}: the fan runs because of the temperature.`,"fan.temp_inactive":`Now {temp}: below the limit.`,"fan.run_on_title":`Own run-on time after the last motion`,"fan.run_on_hint":`How long the fan keeps running once there is no more motion.`,"fan.run_on_default":`Off: the fan runs on for as long as the grace period ({time}).`,"fan.run_on_until":`Fan goes off at`,"fan.shared_via":`shared via {room}`,"fan.share_title":`Share with`,"fan.share_add":`Room`,"fan.share_none":`Do two similar rooms (e.g. two toilets) use one fan? Then share it.`,"fan.share_hint":`The rooms sharing a fan have one activity together: it starts at the first motion in any of them and the steps keep going while there is motion in at least one room. Only when none of the rooms has motion does the run-on time start; then the fan goes off. Sharing works both ways.`,"fan.steps_shared":`No own steps: the steps of {room} are used ({steps}).`,"alarm.motion_only_no_sensor":`This room has no motion sensor: lights switched on will go off after the grace period.`,"alarm.motion_only_active":`Now active: lights react to motion only.`,"alarm.pick_required":`Pick the alarm panel; until then these options do nothing.`,"alarm.last_off":`Alarm last switched the lights off:`,"alarm.never_off":`The alarm has not switched the lights off yet (since the last restart).`,"alarm_state.disarmed":`Disarmed`,"alarm_state.armed_home":`Armed home`,"alarm_state.armed_away":`Armed away`,"alarm_state.armed_night":`Armed night`,"alarm_state.armed_vacation":`Armed vacation`,"alarm_state.arming":`Arming`,"alarm_state.pending":`Pending`,"alarm_state.triggered":`Triggered`,"settings.alarm":`Alarm`,"settings.alarm_hint":`The alarm panel for the whole house. Rooms without their own alarm panel use this one.`,"settings.alarm_panel":`Alarm panel`,"settings.alarm_none":`None`,"settings.dim_armed_home":`Dim at Armed Home (all rooms)`,"settings.dim_armed_home_hint":`While the alarm is on Armed Home all rooms are on Dim; each room can overrule this.`,"settings.dim_armed_home_needs_alarm":`Pick the alarm panel first.`,"alarm.dim_title":`Dim at Armed Home`,"alarm.dim_default":`General ({state})`,"alarm.dim_on":`Always`,"alarm.dim_off":`Never`,"alarm.dim_state_on":`on`,"alarm.dim_state_off":`off`,"alarm.dim_default_tip":`Follow the general setting 'Dim at Armed Home (all rooms)'`,"alarm.dim_on_tip":`This room always dims at Armed Home, whatever the general setting`,"alarm.dim_off_tip":`This room never dims at Armed Home, whatever the general setting`,"alarm.now":`Now`,"alarm.panel_general":`from the general settings`,"alarm.panel_own":`own choice for this room`,"alarm.panel_none":`No alarm panel chosen yet`,"alarm.panel_pick_other":`Choose another panel`,"alarm.panel_use_general":`Use the general panel`,"alarm.panel_remove":`Remove panel`,"alarm.opt_none":`Nothing`,"alarm.opt_none_hint":`Lamps work as usual`,"alarm.opt_off":`All off`,"alarm.opt_off_hint":`Off as soon as this state starts`,"alarm.opt_motion":`Motion only`,"alarm.opt_motion_hint":`Only on with motion, off after the grace period`,"alarm.both_old":`This room had both 'Off at Armed Home' and 'Motion only' on; that stays until you make a choice here.`,"alarm.dim_also":`And burn dimmed`,"alarm.dim_default_card":`Follow the setting for all rooms`,"alarm.dim_on_card":`Lamps burn dimmed in this state`,"alarm.dim_off_card":`Lamps burn at their normal level`,"lux.dark_title":`Dark from`,"lux.mode_title":`Combine sensors`,"lux.combined":`Combined`,"lux.mode_average":`Average`,"lux.mode_min":`Lowest`,"lux.mode_max":`Highest`,"lux.mode_median":`Median`,"lux.mode_sum":`Sum`,"lux.mode_average_hint":`The average of all sensors counts.`,"lux.mode_min_hint":`The darkest sensor counts: the room is dark as soon as one spot is dark.`,"lux.mode_max_hint":`The brightest sensor counts: the room is only dark when it is dark everywhere.`,"lux.mode_median_hint":`The middle value counts; one odd sensor (e.g. in the sun) hardly matters.`,"lux.mode_sum_hint":`All sensor values are added up. Set the thresholds and target lux to match.`,"lux.always":`always`,"lux.dark_hint":`Below {lux} lx this room counts as dark: only then do motion and the door sensor switch the lights on.`,"lux.dark_hint_always":`0 = the room always counts as dark.`,"lux.is_dark":`dark`,"lux.is_light":`light enough`,"lux.control_title":`Light up to target lux`,"lux.control_hint":`While it is light outside, RoomControl keeps checking the lux and dims or brightens the lamps (not pinned ones) in small steps until the target is reached. Once it is dark the standard brightness is used.`,"lux.default_title":`Standard brightness`,"lux.not_set":`not set`,"lux.default_hint":`Lamps that RoomControl switches on go to this level. Once it is dark (sun down) this is used instead of lux control; lamps that are on then switch to it.`,"daylight.rgb_title":`Colour lamps change colour (RGB)`,"daylight.rgb_hint":`Lamps that support colour get the sun's colour as RGB (like Adaptive Lighting's prefer_rgb_color); other lamps get a colour temperature within their own range.`,"daylight.rgb_none":`None of this room's lamps supports colour.`,"daylight.warmest":`Warmest`,"daylight.coolest":`Coolest`,"groups.schedule_keys":`Schedule block data for Dim:`,"groups.or":`or`,"dim.button":`Dim`,"ha_name.label":`Name in Home Assistant`,"ha_name.hint":`Shown on the room's device as`,"ha_name.covers_default":`Gordijnen`,"ha_name.fans_default":`Ventilator`,"bundles.add":`New bundle`,"bundles.default_name":`Bundle`,"bundles.none":`No lamps yet. Choose 'New bundle' and select one or more lamps: they become a bundle with its own settings and its own light in Home Assistant.`,"bundles.pick":`Select the lamps for the new bundle`,"bundles.no_free":`All lamps of this area are already in a bundle (or the area has no lamps in Home Assistant).`,"bundles.settings":`Settings of this bundle`,"bundles.expand":`Expand bundle`,"bundles.collapse":`Collapse bundle`,"bundles.brightness":`Brightness`,"bundles.mode_default":`Standard`,"bundles.mode_fixed":`Fixed`,"bundles.default_hint":`Use the slider above to choose the brightness for motion and times. Choose Fixed to keep the lamps at one level always.`,"bundles.default_level":`This bundle still has its own standard level of {pct}%.`,"bundles.default_level_clear":`Clear`,"bundles.fixed_hint":`Always this level: ignores the brightness slider and the lux sensor.`,"bundles.daylight_on":`Colour follows the sun`,"bundles.when_on":`When on`,"bundles.on_motion":`With motion`,"bundles.no_motion_sensor":`This room has no motion sensor yet.`,"bundles.on_door":`When the door opens (and it is dark)`,"bundles.no_door_sensor":`This room has no door sensor yet.`,"bundles.on_dusk":`When it gets dark`,"bundles.on_dusk_hint":`On at the moment it gets dark (the sun sets).`,"bundles.follow_schedule":`Follows the schedule`,"bundles.follow_schedule_hint":`Not on outside the active schedule, off when it ends. Off = this bundle may always be on.`,"bundles.dim_lux":`Dim and lux`,"bundles.dim":`Takes part in Dim`,"bundles.dim_hint":`With the Dim button, Dim at Armed Home and a time slot's Dim time.`,"bundles.lux":`Light up to the target lux`,"bundles.lux_hint":`In daytime RoomControl adjusts these lamps to {target} lx.`,"bundles.lux_target_off":`Target lux is switched off for this room.`,"bundles.no_lux_sensor":`Add a lux sensor to this room first.`,"bundles.delete":`Delete bundle`,"door.per_bundle":`Which lamps go on when a door opens is set per bundle under Lamps (When on → door).`,"lux.target_title":`Target lux (for bundles with lux control)`,"lux.target_on_hint":`During the day, bundles with lux control adjust their lamps towards this value.`,"lux.target_off_hint":`Off: no lux control in this room, not even for bundles that have it switched on.`,"room.schedules_none_in_area":`No schedules in this area. Create one under Settings → Devices & services → Helpers → Schedule and pick this area in the schedule's settings.`,"room.selector_none_in_area":`No input_number in this area. Create one under Settings → Devices & services → Helpers → Number and pick this area in its settings.`,"alarm.question_state":`When the alarm goes to {state}`,"alarm.opt_on":`All on`,"alarm.opt_on_hint":`On as soon as this state starts, if it is dark`,"alarm.dim_yes":`Yes`,"alarm.dim_no":`No`,"alarm.dim_short":`dimmed`,"alarm.sum_none":`In short: at {state} the alarm changes nothing about the lamps here.`,"alarm.sum_none_dim":`In short: at {state} the lamps here burn dimmed; nothing else changes.`,"alarm.sum_off":`In short: at {state} the lamps here go off.`,"alarm.sum_off_dim":`In short: at {state} the lamps here go off; if they go on again, they burn dimmed.`,"alarm.sum_on":`In short: at {state} the lamps here go on if it is dark.`,"alarm.sum_on_dim":`In short: at {state} the lamps here go on dimmed if it is dark.`,"alarm.sum_motion":`In short: at {state} the lamps here only go on with motion.`,"alarm.sum_motion_dim":`In short: at {state} the lamps here only go on with motion, and then dimmed.`,"fan.change":`Change`,"fan.when":`When does the fan go on?`,"fan.trigger_motion":`With motion`,"fan.trigger_motion_hint":`Faster the longer it lasts`,"fan.trigger_temp":`By temperature`,"fan.trigger_temp_hint":`From a set temperature`,"fan.trigger_manual":`Manual only`,"fan.trigger_manual_hint":`RoomControl does not drive the fan`,"fan.steps_title":`With motion: speed per step`,"fan.reason_activity":`activity`,"fan.reason_temp":`temperature`,"fan.run_on_how_long":`How long to run on`,"fan.run_on_grace":`Grace period`,"fan.run_on_own":`Own time`,"fan.run_on_own_hint":`Choose yourself`,"fan.sum_prefix":`In short: the fan runs`,"fan.sum_motion":`with motion (from {from} to {to})`,"fan.sum_temp":`from {lo} degrees at {speed}`,"fan.sum_and":`, and `,"fan.sum_highest":`; the highest speed counts.`,"fan.sum_run_on":`Run-on: {time}.`,"fan.sum_manual":`In short: RoomControl does not drive the fan; you operate it yourself.`,"fan.level_low":`Low`,"fan.level_medium":`Medium`,"fan.level_high":`High`,"fan.nobody_home":`Nobody home: the fan stays off.`,"fan.presence_rule":`When nobody is home, the fan stays off.`,"fan.expand":`Expand fan settings`,"fan.status_label":`Fan`,"fan.status_off":`off`,"fan.status_step":`step {n} of {total}`,"fan.status_until":`off at`,"fold.expand":`Expand`,"fold.schedules":`{n} schedule(s) · active now: {active}`,"fold.none_active":`none`,"fold.presence_none_enabled":`No persons chosen in the settings yet`,"fold.presence_none":`No persons linked: presence does not matter`,"fold.home":`home`,"fold.away":`away`,"fold.motion":`{n} sensor(s) · {state}`,"fold.lux":`{n} sensor(s) · now {lux}`,"fold.covers":`{n} curtain(s) · {follow}`,"fold.covers_follow":`follow dark/light`,"fold.covers_manual":`by hand only`,"lux.sensor_chip":`Sensor`,"lux.mode_question":`How do the sensors count?`,"lux.target_off_title":`Off`,"lux.target_off_card":`No lux control`,"lux.target_on_title":`On`,"lux.target_on_card":`Adjust during the day`,"lux.sum_now_light":`In short: {how} {lux} lx, so light enough.`,"lux.sum_now_dark":`In short: {how} {lux} lx, so dark.`,"lux.sum_single":`now`,"lux.sum_dark":`Dark from {lux} lx.`,"lux.sum_always_dark":`The room always counts as dark.`,"lux.sum_target":`During the day bundles with lux control adjust up to {lux} lx.`,"lux.sum_target_off":`No lux control.`,"lux.alarm_pause_title":`Don't adjust in alarm state`,"lux.alarm_pause_none":`No state chosen: lux control works in every alarm state.`,"lux.alarm_pause_hint":`At {states} RoomControl does not adjust the lamps here.`,"lux.alarm_pause_no_panel":`Choose an alarm panel first (under Alarm or in the settings); until then this does nothing.`,"lux.alarm_paused_now":`Paused now by the alarm state.`,"lux.sum_alarm_pause":`Not at {states}.`,"fold.selector_missing":`input_number missing (required)`,"info.show":`Show explanation`,"info.hide":`Hide explanation`,"info.lights":`Lamps live in bundles. A bundle is one or more lamps that share the same settings: how bright they go on, whether they follow daylight, and when they go on (with motion, the door, or in their own time slots). Each bundle also becomes its own light in Home Assistant.`,"info.schedules":`A schedule (a Home Assistant helper) decides when light belongs here. While it is on, bundles that follow it are on at their level; during the day bundles with lux control aim for the target lux. Outside the schedule light goes on with motion: when the sun is down, or during the day when it is darker than 'Dark from'. With two or more schedules an input_number picks which one applies (1 = first, 0 = no limit).`,"info.links":`Linked rooms share their motion: motion in one room keeps the light on in the other too. Handy for an open kitchen and living room, or a hall and landing. Links work both ways.`,"info.presence":`Choose which persons belong to this room. When none of them is home, lights here do not go on automatically. Without linked persons presence does not matter.`,"info.motion":`Motion sensors switch the light on when it is dark, and off after the grace period without motion. With several sensors, motion on any of them counts. You also set the grace period here.`,"info.doors":`A door sensor switches the light on as soon as the door opens and it is dark, like motion. Per bundle you choose whether it reacts to the door.`,"info.alarm":`When disarmed the lamps follow time slots, sun and motion. At Armed Home they go off, except where there is motion (at Dim). At Armed Away (nobody home) they go off, unless you choose 'Keep on, follow time slot' for this room: then the lamps follow the bundle's time slot and go off when it ends.`,"info.lux":`Lux sensors measure how light it is. 'Dark from' decides when motion and the door switch the light on. With the target lux, bundles with lux control adjust their lamps to that value during the day. With several sensors you choose how they count.`,"info.fan":`The fan can go on with motion (faster the longer it lasts), from a temperature, or only by hand. After the last motion it runs on for a while. When nobody is home it stays off. Two rooms can share one fan.`,"info.covers":`Add this room's curtains or screens. Open, Stop and Close operate them all at once. With 'Follow dark/light' they close at dusk or dark and open at sunrise or a fixed time.`,"bundles.t_motion":`Motion`,"bundles.t_door":`Door`,"bundles.t_dusk":`Dark`,"bundles.t_schedule":`Schedule`,"bundles.when_question":`When do these lamps go on?`,"bundles.when_info":`With own times the time slot wins: while a slot runs the bundle is on at its level (during the day with lux control: the target lux). Outside its slots motion and the door switch the bundle on when the sun is down, or during the day when it is darker than 'Dark from'.`,"bundles.one_lamp":`1 lamp`,"bundles.n_lamps":`{n} lamps`,"bundles.lamp_chip":`Lamp`,"bundles.sub_by_hand":`by hand only`,"bundles.sub_daylight":`daylight`,"bundles.sub_fixed":`fixed {pct}%`,"bundles.sub_default":`standard`,"bundles.mode_default_card":`The lamp's own level`,"bundles.mode_fixed_card":`Always this level`,"bundles.colour":`Colour`,"bundles.colour_own":`Own colour`,"bundles.colour_own_card":`The lamp decides`,"bundles.extra":`Extra`,"bundles.extra_dim":`Takes part in Dim`,"bundles.extra_lux":`Lux control`,"bundles.sum_when":`In short: {name} goes on with {when}.`,"bundles.sum_fixed":`Always at {pct}%,`,"bundles.sum_default":`At its own level,`,"bundles.sum_daylight":`in the colour of daylight.`,"bundles.sum_own_colour":`in its own colour.`,"bundles.sum_dim":`Takes part in Dim.`,"bundles.sum_lux":`Adjusted to lux during the day.`,"info.dim_codes_title":`Dimming from the schedule:`,"info.dim_codes_where":`put one or more of these lines in the additional data (YAML) of a time block of the schedule helper. While that block is active, those lamps are dimmed.`,"info.dim_code_all":`all bundles that take part in Dim`,"info.dim_code_bundle_name":`bundle {name}`,"ha_name.label_lights":`Name of the light that controls the whole room`,"overview.lit":`Light is on in {n} of {total} rooms`,"overview.n_links":`{n} link(s)`,"overview.none_on":`No lights on anywhere`,"overview.linked":`Linked`,"overview.kind_motion":`Motion`,"overview.kind_fan":`Fan`,"overview.kind_motion_hint":`motion in one room keeps the light on in the other`,"overview.kind_fan_hint":`one fan for these rooms`,"overview.edge_motion":`direct`,"overview.edge_fan":`shares`,"overview.n_on":`light on in {n}`,"overview.via":`{a} and {b} via {through}`,"settings.alarm_fixed":`Disarmed: the lamps follow time slots, sun and motion. Armed Home: the lamps go off, except where there is motion (at Dim), off after the grace period. Armed Away: all lamps off, except in rooms that aren't switched off when nobody is home; those follow the bundle's time slot.`,"settings.sun":`Sun`,"settings.sun_hint":`This sun entity decides for all rooms whether the sun is down.`,"settings.sun_entity":`Sun entity`,"settings.sun_down":`Now: sun down`,"settings.sun_up":`Now: sun up`,"settings.sun_missing":`Not found: add the Sun integration in Home Assistant.`,"bundles.evening_hint":`While a time slot runs and the sun is down, the bundle burns at this level.`,"alarm.fixed_disarmed":`The lamps follow time slots, sun and motion as set.`,"alarm.fixed_home":`The lamps go off, except where there is still motion. With motion on at Dim, off after the grace period.`,"alarm.fixed_away":`The lamps go off and stay off while nobody is home.`,"alarm.fixed_other":`This alarm state does not change the lamps.`,"motion_note.armed_away":`the alarm is on Armed Away`,"motion_note.lux_control":`the schedule is on: the target lux drives the lamps`,"motion_note.sun_up":`the sun is up and it is not dark enough`,"card.bundle":`bundle`,"card.bundles":`bundles`,"card.sun_down":`Dark: the sun is down`,"card.sun_up":`Light`,"card.link_motion":`Link {n}: shared motion`,"card.link_fan":`Link {n}: shared fan`,"clock.section":`Alarm clocks`,"clock.add":`Alarm clock`,"clock.none":`No alarm clocks yet`,"clock.default_name":`Alarm clock`,"clock.time":`Time`,"clock.name":`Name`,"clock.days":`Days (every week)`,"clock.day_0":`Mon`,"clock.day_1":`Tue`,"clock.day_2":`Wed`,"clock.day_3":`Thu`,"clock.day_4":`Fri`,"clock.day_5":`Sat`,"clock.day_6":`Sun`,"clock.once":`Once`,"clock.every_day":`every day`,"clock.no_days":`no days`,"clock.days_hint":`The alarm clock repeats every week on the chosen days. Once: it goes off one time and then switches itself off.`,"clock.persons":`Only when home`,"clock.persons_none":`Choose persons for alarm clocks in the settings ('Alarm clock' tick) first; until then the alarm clock always goes off.`,"clock.persons_chosen":`The alarm clock only goes off when at least one of these persons is home.`,"clock.persons_room":`Nothing chosen: the room's persons count ({names}).`,"clock.persons_anyone":`Nothing chosen and no persons for the room: the alarm clock always goes off.`,"clock.bundles":`Bundles`,"clock.no_bundles":`no bundles`,"clock.snooze":`Step by step`,"clock.snooze_on":`Step by step on`,"clock.snooze_off_hint":`Off: at the set time the lamps go on at 100% straight away.`,"clock.snooze_on_hint":`On: the light starts soft and gets one step brighter each interval.`,"clock.sub_snooze":`step by step {n}×`,"clock.snoozes":`Number of steps`,"clock.snooze_minutes":`Interval`,"clock.snooze_n":`step {n}`,"clock.snooze_hint":`It goes to 100% by itself in equal steps: one step further each interval. You don't have to press anything. The alarm clock's stop button switches it off.`,"clock.music_title":`Music`,"clock.music":`music`,"clock.no_music":`no music`,"clock.no_players":`No media player in this room and no Music Assistant player without a room. Assign a player to the area in Home Assistant.`,"clock.player":`Media player`,"clock.media":`What plays`,"clock.media_chosen":`Chosen`,"clock.ha_hint":`In Home Assistant, the room's device has a 'stop' button and an on/off switch for each alarm clock.`,"clock.summary":`In short: {days} at {time} {bundles} go on at {first}%, then in {n} step(s) of {min} min up to 100%.`,"clock.summary_direct":`In short: {days} at {time} {bundles} go straight on at 100%.`,"clock.summary_music":`Music on {player}, louder with every step.`,"clock.summary_stop":`Without reaction, at the stop step at {time}: {what}.`,"clock.delete":`Delete alarm clock`,"info.clocks":`An alarm clock switches the chosen bundles on at the chosen days and time, optionally with music and curtains opening. Without 'Step by step' straight at 100%; with 'Step by step' one step further each interval up to 100%. It only goes off when one of the chosen persons is home.`,"clock.music_on":`Music on`,"clock.music_off_hint":`Off: the alarm clock only switches the light on.`,"clock.music_on_hint":`On: music on the chosen player, louder with every step.`,"clock.music_pick":`Choose a player and what plays.`,"clock.pick_player":`Choose a player…`,"debug.title":`Debug log`,"debug.sub":`Why bundles do or don't go on/off · newest first · refreshes every 3 s`,"debug.empty":`Nothing logged since the last restart.`,"debug.kind.on":`On`,"debug.kind.off":`Off`,"debug.kind.adjust":`Adjusted`,"debug.kind.ignored":`Ignored`,"debug.kind.blocked":`Not on`,"debug.kind.info":`Info`,"debug.reason.motion":`motion`,"debug.reason.door":`door opened`,"debug.reason.schedule_sun_down":`schedule on, sun down`,"debug.reason.alarm_off_schedule_sun_down":`alarm off, schedule on, sun down`,"debug.reason.schedule_ended":`schedule ended`,"debug.reason.nobody_home":`nobody home`,"debug.reason.no_motion":`no motion (grace period over)`,"debug.reason.alarm_armed_home":`alarm Armed Home`,"debug.reason.alarm_armed_away":`alarm Armed Away`,"debug.reason.lux_dark":`too dark for the target lux`,"debug.reason.lux_bright":`too light, the lamps make no difference`,"debug.reason.lux_brighter":`brighter towards the target lux`,"debug.reason.lux_dimmer":`dimmer towards the target lux`,"debug.reason.alarm_clock":`alarm clock`,"debug.reason.manual_start":`manual control started`,"debug.reason.manual_end":`manual control ended`,"debug.reason.manual_control_ended_lights_not_allowed_now":`manual ended: light not allowed now`,"debug.reason.manual_control_ended_motion":`manual ended: motion`,"debug.reason.external_on":`switched on outside RoomControl (switch, app, automation)`,"debug.reason.conditions":`conditions changed`,"debug.why.manual":`manual control is on`,"debug.why.armed_home":`alarm on Armed Home (motion only)`,"debug.why.armed_away":`alarm on Armed Away`,"debug.why.nobody_home":`nobody home`,"debug.why.schedule":`the schedule doesn't allow it`,"debug.target":`target`,"debug.clock":`alarm clock`,"debug.schedule":`schedule`,"debug.sun":`sun`,"debug.home":`someone home`,"debug.v_on":`on`,"debug.v_off":`off`,"debug.v_down":`down`,"debug.v_up":`up`,"debug.v_yes":`yes`,"debug.v_no":`no`,"debug.now":`Now`,"debug.now_schedule":`Schedule`,"debug.now_no_schedule":`none (counts as schedule off)`,"debug.now_sun":`Sun`,"debug.now_missing":`not found`,"debug.now_alarm":`Alarm`,"debug.now_home":`Someone home`,"debug.now_manual":`Manual`,"debug.now_motion":`Motion now`,"debug.now_lux":`Lux`,"debug.now_dark_from":`dark from`,"debug.now_bundles":`Per bundle: what RoomControl wants now`,"debug.alarm_normal":`disarmed / none`,"debug.alarm_home":`Armed Home`,"debug.alarm_away":`Armed Away`,"debug.wants_lux":`lux control drives it (on when too dark)`,"debug.wants_motion":`goes on with motion`,"debug.wants_off_schedule":`stays off (schedule off, sun up)`,"debug.wants_off_away":`stays off (Armed Away)`,"debug.wants_motion_1pct":`motion only, at Dim (Armed Home)`,"debug.wants_nothing":`nothing automatic (e.g. too light, or the bundle doesn't follow motion)`,"debug.flag_schedule":`follows schedule`,"debug.flag_no_schedule":`doesn't follow schedule`,"debug.flag_motion":`motion`,"debug.flag_lux":`lux control`,"motion_note.schedule":`the schedule is on: bundles that follow it are on at their level`,"debug.wants_on_schedule":`should be on (schedule on; the schedule wins over motion)`,"debug.reason.schedule":`schedule on`,"alarm.fixed_away_ignored":`This room isn't switched off when nobody is home. The lamps follow the bundle's time slot and go off when it ends.`,"bundles.move_up":`Move up`,"bundles.move_down":`Move down`,"analysis.period_3d":`3 days`,"analysis.period_max":`{n} days (max)`,"analysis.kept":`Home Assistant keeps {n} days`,"analysis.light_on":`light on`,"analysis.schedule_on":`schedule on`,"analysis.on_in_schedule":`of schedule time on`,"analysis.on_outside":`on outside schedule`,"analysis.lg_schedule":`Schedule`,"analysis.lg_sun":`sun down`,"analysis.lg_light":`light on`,"analysis.lg_light_short":`Light`,"analysis.lg_lux":`lux`,"analysis.tap_block":`Hover over the chart for the values; tap an orange strip (light on) for time, bundle and reason. Tap a legend item to hide it.`,"analysis.chart_label":`Timeline: schedule, sun, light on and lux`,"analysis.in_schedule":`during the schedule`,"analysis.partly_schedule":`partly during the schedule`,"analysis.outside_schedule":`outside the schedule`,"analysis.no_reason":`No reason known (only for recent blocks since the last restart).`,"analysis.taller":`Taller`,"analysis.smaller":`Smaller`,"analysis.zoom":`Zoom`,"analysis.scroll_hint":`Scroll the chart sideways to see the rest of the period.`,"settings.late_home":`Home-later button for {name}`,"room.late_home":`Keep on for Home later`,"room.late_home_off":`Off: the bundles follow the normal rules, also when someone comes home later.`,"room.late_home_on":`On: while a 'Home later' button is on, the bundles here don't go off until that person is home.`,"room.late_home_active":`Active now for: {names}`,"debug.why.late_home":`'Home later' is on: the bundles stay on`,"debug.reason.late_home_arrived":`home later: arrived`,"late.title":`Home later`,"late.active":`on`,"late.restart":`Restart Home Assistant to create this button.`,"late.is_home":`{name} is home; Home later only works while someone is away.`,"late.on_hint":`On: rooms with 'Keep on for Home later' stay on until this person is home. Click to switch off.`,"late.off_hint":`Click to switch on: rooms with 'Keep on for Home later' stay on until this person is home.`,"settings.late_home_short":`Home later`,"alarm.home_choose":`Choose what the lamps in this room do:`,"alarm.home_motion":`On motion, dimmed`,"alarm.home_no_motion":`Not on motion`,"alarm.fixed_home_no_motion":`The lamps go off and don't react to motion, but do react to the rest: the alarm clock, curtains opening and switching on by hand.`,"debug.why.armed_home_no_motion":`alarm on Armed Home (not on motion)`,"debug.wants_armed_home_no_motion":`not on motion; alarm clock and by hand do work (Armed Home)`,"motion_note.armed_home_no_motion":`the alarm is on Armed Home and this room doesn't react to motion then`,"media.section":`Media players`,"media.add":`Add media player`,"media.none":`No media players`,"media.none_in_area":`No media players in this area. Assign them to the area in Home Assistant first.`,"media.play":`Play`,"media.pause":`Pause`,"media.state_playing":`Playing`,"media.state_paused":`Paused`,"media.state_idle":`Idle`,"media.state_on":`On`,"media.state_off":`Off`,"media.state_standby":`Standby`,"media.state_buffering":`Buffering…`,"media.state_unavailable":`Unavailable`,"fold.media":`{n} media player(s)`,"fold.media_playing":`{n} media player(s) · {playing} playing`,"info.media":`Add this room's media players, such as a TV or speaker. You see what's playing and can play or pause. They don't change the lamps or other rules (yet).`,"clock.player_room":`Plays on {player}, this room's media player (Media players section).`,"clock.player_room_many":`From this room's media players (Media players section).`,"covers.inverted":`Reversed`,"covers.inverted_chip":`reversed`,"covers.inverted_on":`On: RoomControl swaps Open and Close for this curtain.`,"covers.inverted_off":`Off: Open and Close go as Home Assistant sends them.`,"covers.test":`Test direction`,"covers.test_btn":`Test`,"covers.test_hint":`Sends the curtain open for 3 seconds, then stops.`,"covers.test_running":`Curtain opening for 3 seconds…`,"covers.test_question":`Did the curtain open?`,"covers.test_yes":`Yes, correct`,"covers.test_no":`No, it closed: reverse`,"fold.lights":`{n} bundle(s) · {on} on`,"bundles.none_short":`No bundles yet`,"fold.doors":`{n} door sensor(s) · {state}`,"settings.clock_person":`{name} can be chosen on alarm clocks`,"settings.clock_person_short":`Alarm clock`,"clock.covers_title":`Curtains`,"clock.covers_on":`Open curtains`,"clock.covers_on_hint":`On: the curtains open in the 'Step by step' steps.`,"clock.covers_off_hint":`Off: the alarm clock leaves the curtains alone.`,"clock.covers_same":`Light and curtains together`,"clock.covers_own":`Set separately`,"clock.covers_hint":`Curtains without a position open fully at the first step. Stopping the alarm clock leaves the curtains where they are.`,"clock.sub_covers_same":`curtains along`,"clock.sub_covers_own":`curtains separate`,"clock.snooze_off_hint_covers":`Off: at the set time the lamps go on at 100% and the curtains open fully straight away.`,"clock.snooze_on_hint_covers":`On: light and curtains start soft and go one step further each interval.`,"clock.steps_light":`Light`,"clock.steps_covers":`Curtains`,"clock.covers_on_hint_direct":`On: the curtains open fully at the alarm time.`,"settings.vacuum_person":`{name} can be chosen on cleaning moments and counts for the vacuum's alarm handling`,"settings.vacuum_person_short":`Vacuum`,"vacuum.section":`Vacuum`,"vacuum.add":`Choose vacuum`,"vacuum.none":`No vacuum chosen yet.`,"vacuum.none_in_area":`No vacuum found in Home Assistant.`,"vacuum.add_plan":`Add moment`,"vacuum.no_plans":`No cleaning moments yet. Choose 'Add moment'.`,"vacuum.now":`Clean now`,"vacuum.start_failed":`The vacuum could not start.`,"vacuum.done_today":`Vacuumed today`,"vacuum.not_today":`Not vacuumed today`,"vacuum.last":`Last vacuumed:`,"vacuum.never":`Not vacuumed by RoomControl yet`,"vacuum.fold_plans":`{n} moment(s)`,"vacuum.state_cleaning":`Cleaning`,"vacuum.state_docked":`Docked`,"vacuum.state_idle":`Idle`,"vacuum.state_paused":`Paused`,"vacuum.state_returning":`Returning`,"vacuum.state_error":`Error`,"vacuum.state_unavailable":`Unavailable`,"vacuum.default_name":`Cleaning moment`,"vacuum.sub_always":`always`,"vacuum.sub_retry":`else later, until {time}`,"vacuum.sub_waiting":`waiting until everybody left`,"vacuum.retry":`Try later`,"vacuum.retry_on":`On: if it isn't allowed at the moment, it starts as soon as it is, until {time}.`,"vacuum.retry_off":`Off: if it doesn't fit at the moment, it skips this moment.`,"vacuum.retry_until":`Until`,"vacuum.next":`Next time:`,"vacuum.waiting":`Waiting until everybody left (until {time}).`,"vacuum.delete_plan":`Delete moment`,"vacuum.alarm_hint":`If it starts while nobody is home, RoomControl first sets the alarm to Armed Home. When it's done and still nobody is home, the alarm goes to Armed Away. If somebody is home by then, the alarm is left as it is.`,"vacuum.alarm_none":`Choose an alarm panel in the settings to have the alarm switch along with the vacuum.`,"info.vacuum":`Choose this room's vacuum and plan cleaning moments by time and days, or link a schedule. The icon is green when it was vacuumed today and turns grey when the next day begins.`,"card.vacuumed_today":`Vacuumed today`,"card.vacuum_not_today":`Not vacuumed today`,"vacuum.schedule_on":`Cleaning schedule`,"vacuum.schedule_on_hint":`On: the moments below start the vacuum. Can also be switched in Home Assistant ('Stofzuigschema' switch on the room's device).`,"vacuum.schedule_off_hint":`Off: the vacuum doesn't start by itself. 'Clean now' still works.`,"vacuum.fold_off":`schedule off`,"vacuum.persons_none":`Tick 'Vacuum' at the persons in the settings to choose them here.`,"vacuum.alarm_states":`Or allowed in alarm state`,"vacuum.alarm_states_chosen":`Or when the alarm is in one of these states.`,"vacuum.alarm_states_any":`Nothing chosen. With nothing chosen for persons and alarm, it's always allowed.`,"vacuum.alarm_states_no_panel":`Choose an alarm panel in the settings; until then these states don't count.`,"bundles.on_from":`On during the schedule`,"bundles.on_from_schedule":`Whole schedule`,"bundles.on_from_schedule_hint":`On as long as the schedule runs`,"bundles.on_from_dusk":`From dusk`,"bundles.on_from_dusk_hint":`On when dusk begins`,"bundles.on_from_dark":`From dark`,"bundles.on_from_dark_hint":`On when it is dark`,"bundles.dusk_ramp":`No lux sensor: during dusk the bundle gradually gets brighter up to {pct}%, along with the sun. When it is dark it burns at its normal level.`,"bundles.dusk_lux":`With lux sensor: during dusk the bundle works towards the room's target lux. When it is dark it burns at its normal level.`,"covers.close_at":`Close at`,"covers.close_at_dusk":`Dusk`,"covers.close_at_dark":`Dark`,"covers.open_at":`Open at`,"covers.open_at_auto":`With the schedule`,"covers.open_at_never":`Not automatically`,"covers.open_at_light":`Light`,"covers.open_at_time":`Fixed time`,"covers.open_at_light_hint":`Open when the sun rises (Sun integration).`,"covers.open_at_time_hint":`Open at this time, also when it is still dark.`,"covers.open_at_auto_hint":`Open when the schedule starts and it is light.`,"covers.open_at_never_hint":`The curtains are not opened automatically.`,"settings.dusk_elevation":`Dusk from sun elevation`,"settings.dusk_now":`Now: sun at {deg}° · {phase}`,"settings.dusk_hint":`Dusk starts when the sun is lower than this elevation; dark starts when the sun sets. Bundles and curtains can react to dusk or dark.`,"phase.light":`light`,"phase.dusk":`dusk`,"phase.dark":`dark`,"card.sun_dusk":`Dusk: the bundles on from dusk are burning`,"debug.v_light":`light`,"debug.v_dusk":`dusk`,"debug.v_dark":`dark`,"bundles.t_own_times":`Times`,"slots.title":`When on`,"slots.none":`No time slots yet: the bundle doesn't go on by itself.`,"slots.start":`Start`,"slots.end":`End`,"slots.start_time":`Time`,"slots.start_dusk":`Dusk`,"slots.start_dark":`Dark`,"slots.until":`until`,"slots.end_time":`Time`,"slots.end_sunrise":`Sunrise`,"slots.add":`Time slot`,"slots.hint":`The bundle goes on when a slot starts, with 'Dim' on, to Dim at that time (the dim level from the settings) and off when the slot ends (with motion: after the grace period). A slot that ends before it starts, or at sunrise, runs into the next day.`,"slots.dusk_ramp":`If a slot starts at dusk, the bundle starts at 0% and slowly gets brighter, along with the sun, up to its own brightness at sunset.`,"slots.dusk_lux":`If a slot starts at dusk, the bundle works towards the target lux during dusk, and when it is dark it burns at its normal level.`,"slots.holiday":`Vacation`,"slots.vacation_on":`vacation is on`,"slots.vacation_off":`vacation is off`,"slots.holiday_hint":`'Normal' slots apply as usual; in Vacation mode (general settings) the 'Vacation' slots apply — a bundle without them keeps its normal ones.`,"settings.vacation":`Vacation`,"settings.vacation_title":`Normal or vacation`,"settings.vacation_on":`Vacation: bundles use their 'Vacation' slots (e.g. off later in the evening). Also the 'Vakantie' switch on the General device in Home Assistant.`,"settings.vacation_off":`Normal: bundles use their 'Normal' slots.`,"settings.vacation_missing":`The 'Vakantie' switch doesn't exist yet; restart Home Assistant after the update.`,"slots.holiday_normal":`Normal`,"slots.holiday_vacation":`Vacation`,"settings.mode_normal":`Normal`,"settings.mode_vacation":`Vacation`,"settings.vacation_alarm":`Link to the alarm`,"settings.vacation_alarm_on":`On: when the alarm is Armed Vacation, the mode goes to Vacation; when it leaves that state, back to Normal. You can still switch the mode yourself.`,"settings.vacation_alarm_off":`Off: you switch the mode yourself (here or with the 'Vakantie' switch in Home Assistant).`,"settings.vacation_alarm_no_panel":`Choose an alarm panel above first.`,"bundles.convert_title":`Replace the room's schedule with times`,"bundles.convert_hint":`These bundles still follow the room's schedule: {names}. Convert them: they get the same days and times as time slots, and the schedule is unlinked.`,"bundles.convert_btn":`Convert`,"bundles.convert_not_found":`The schedule wasn't found in Home Assistant (only schedules made in the UI can be taken over).`,"bundles.convert_failed":`Converting didn't work.`,"slots.name":`Name of the time slot`,"slots.name_placeholder":`Time slot`,"settings.dim":`Dim`,"settings.dim_level":`Dim level`,"settings.dim_level_hint":`How bright lamps burn when Dim is on: the Dim button, Dim at Armed Home and 'Dim from' in a time slot (when it has no level of its own). Default 1%.`,"slots.dim_at":`at`,"slots.dim":`Dim`,"analysis.lg_target":`target lux`,"analysis.tip_light_on":`light on`,"analysis.tip_light_off":`light off`,"analysis.tip_sched_off":`no schedule`,"analysis.tip_sun_down":`sun down`,"analysis.tip_sun_up":`sun up`,"bundles.convert_unused":`This room still has a schedule, but no bundle uses it any more. Unlink it (the curtains then only close at dusk or dark).`,"bundles.unlink_btn":`Unlink`,"vacuum.home_persons":`Allowed when home`,"vacuum.home_chosen":`Allowed when at least one of these persons is home.`,"vacuum.home_anyone":`Nobody chosen.`,"vacuum.sub_home":`when {names} is home`,"vacuum.sub_alarm":`in {states}`,"vacuum.or":`or`,"clock.summary_no_stop":`It doesn't stop by itself.`,"clock.volume_first":`Volume first step`,"clock.volume_last":`Volume last step`,"clock.stop_step":`stop step`,"clock.stop_music":`Music off`,"clock.stop_light":`Light off`,"clock.stop_what_both":`music and light off`,"clock.stop_what_music":`music off`,"clock.stop_what_light":`light off`,"clock.stop_what_none":`doesn't stop`,"clock.stop_hint":`The stop step follows one interval after the last step, if nobody stopped the alarm clock.`,"clock.stop_none_warn":`Nothing ticked at the stop step: the alarm clock doesn't stop by itself.`,"clock.pill_steps":`{n} steps`,"clock.pill_every":`every {min} min`,"clock.pill_direct":`Straight to 100%`,"clock.pill_off":`Off`,"clock.pill_open":`Open`,"clock.pill_covers_same":`Together with light`,"clock.pill_covers_own":`Separate`,"clock.pill_covers_direct":`Straight open`,"clock.pill_pick":`Pick player and music`,"locks.section":`Locks`,"locks.add":`Add lock`,"locks.none":`No locks`,"locks.none_in_area":`No locks in this area. Assign them to the area in Home Assistant first.`,"locks.fold":`{n} lock(s) · {locked} locked`,"locks.hint":`RoomControl only ever locks a lock by itself, never opens it. In Home Assistant every lock is also on the room's device.`,"info.locks":`Add the locks of this room. Per lock you set the times it gets locked, whether it locks when nobody is home, and whether the panel asks before it opens.`,"locks.state_locked":`Locked`,"locks.state_open":`Open`,"locks.state_jammed":`Jammed`,"locks.state_moving":`Busy…`,"locks.state_unknown":`Unknown`,"locks.open":`Open`,"locks.lock":`Lock`,"locks.since":`since`,"locks.confirm_q":`Are you sure you want to open {name}?`,"locks.cancel":`Cancel`,"locks.confirm_yes":`Yes, open`,"locks.options":`Options`,"locks.away":`Lock when nobody is home`,"locks.away_hint":`When everybody (persons in the general settings) has been away for {min} min, the lock locks. Also when it opens while nobody is home.`,"locks.away_after":`Wait`,"locks.confirm":`Confirm before opening`,"locks.confirm_hint":`The panel asks first whether the lock really should open. In Home Assistant it opens straight away.`,"locks.never_opens":`Set times and 'nobody home' only lock this lock, never unlock it.`,"locks.remove":`Remove lock`,"locks.pill_no_slots":`No times`,"locks.pill_slots_off":`All times off`,"locks.pill_away":`Nobody home · {min} min`,"locks.pill_confirm":`Confirm to open`,"locks.times_title":`When locked`,"locks.times_none":`No times yet: the lock doesn't lock at set times.`,"locks.times_hint":`At this time the lock locks, on the chosen days. If it is locked already, nothing happens. Use the switch to turn a time off without removing it.`,"locks.time_at":`Lock at`,"locks.time_add":`Time`,"locks.time_name_placeholder":`Time`,"alarm.away_choose":`Nobody is home. Choose what the lamps in this room do:`,"alarm.away_off":`Switch off`,"alarm.away_follow":`Keep on, follow time slot`,"locks.time_on":`This time on`,"locks.time_off":`Off`,"smart.section":`Smart`,"info.smart":`Smart options learn from how the room is used. Everything stays local in Home Assistant. The room's behaviour (when lamps are on, motion per hour) is always recorded, so an option has data as soon as you switch it on.`,"smart.fold_none":`No smart options on`,"smart.fold":`{n} smart option(s) on`,"smart.forget":`Learn again`,"smart.needs_motion":`Only works with a motion sensor in this room.`,"smart.needs_media":`Add a media player to this room first.`,"smart.grace":`Grace period learns`,"smart.grace_hint":`If the lamps go off and there is motion again within a minute, the grace period gets 1 minute longer. If the off was right, it slowly gets shorter again (up to 15 minutes extra).`,"smart.grace_status":`Now {min} min longer than set`,"smart.grace_status_none":`Nothing learned yet: the set grace period applies`,"smart.media":`Media keeps the room in use`,"smart.media_hint":`While a media player of this room is playing, paused or on, the lamps don't go off for lack of motion.`,"smart.media_status":`Media is playing: the lamps stay on`,"smart.last_motion":`Someone is still here`,"smart.last_motion_hint":`If the last motion in the house was in this room, someone is probably still here. The lamps stay on until there is motion elsewhere, at most 45 minutes. Then the grace period applies.`,"smart.last_motion_status":`Last motion in the house was here: on for {min} more min`,"smart.brightness":`Learn brightness`,"smart.brightness_hint":`When you make a lamp brighter or dimmer by hand, the room remembers it per hour of the day. After three times it becomes the standard brightness for that hour.`,"smart.brightness_status":`{n} lamp-hours learned`,"smart.replay":`Look lived-in`,"smart.replay_hint":`When nobody is home (or the alarm is Armed Away) and it is dark, the lamps go on and off like on the same weekday last time, shifted a few minutes each day.`,"smart.replay_status":`{n} day(s) of behaviour remembered`,"smart.replay_status_active":`Active now: the lamps follow last week's behaviour`,"smart.anomaly":`Report unusual activity`,"smart.anomaly_hint":`A Home Assistant notification for motion at a time when nobody is ever here, and when the lamps have been on for 3 hours without motion. A roomcontrol_anomaly event is fired too, so you can make your own push message.`,"smart.anomaly_status_learning":`Learning ({weeks} weeks): motion alerts after 2 weeks`,"smart.anomaly_status_ready":`{weeks} weeks learned`,"debug.reason.grace_learned":`grace period adjusted`,"debug.reason.brightness_learned":`brightness learned`,"debug.reason.replay":`look lived-in`,"debug.reason.replay_end":`look lived-in stopped`,"debug.reason.anomaly_motion":`unusual motion reported`,"debug.reason.anomaly_lights_on":`lamps on long reported`,"smoke.section":`Smoke detectors`,"smoke.hint":`Choose which smoke detectors RoomControl follows. On smoke in one room, RoomControl does what is switched on below in the whole house, and then nothing automatic until you press 'All safe'.`,"smoke.none":`No smoke detectors found (binary_sensor with device class smoke).`,"smoke.detected":`Smoke!`,"smoke.offline":`Unavailable`,"smoke.battery_low":`Battery low`,"smoke.battery":`battery`,"smoke.clear_state":`No smoke`,"smoke.actions_title":`On smoke, anywhere in the house`,"smoke.action_lights":`All lights fully on`,"smoke.action_lights_hint":`100% in every room, white light where the lamp can. Overrides schedule, alarm, Dim and manual.`,"smoke.action_fans":`Fans off`,"smoke.action_fans_hint":`So smoke is not drawn through the house. They stay off until 'All safe'.`,"smoke.action_covers":`Open curtains`,"smoke.action_covers_hint":`A view outside, and for emergency services a view inside.`,"smoke.action_locks":`Unlock locks`,"smoke.action_locks_hint":`Only when someone is home, to clear the escape route. The only time RoomControl unlocks a lock.`,"smoke.action_media":`Stop media and warn`,"smoke.action_media_hint":`Stop music and TV in the rooms. The announcement speakers say where the smoke is.`,"smoke.action_vacuum":`Vacuum back to its dock`,"smoke.action_vacuum_hint":`So it doesn't block the escape route. Cleaning moments wait until 'All safe'.`,"smoke.action_maintenance":`Notify on low battery or failure`,"smoke.action_maintenance_hint":`A Home Assistant notification when the battery is below 20%, or a detector has been unavailable for 24 hours.`,"smoke.banner_title":`Smoke detected · {where} · {time}`,"smoke.banner_hint":`RoomControl does nothing automatic until you confirm all is safe.`,"smoke.banner_still":`A smoke detector still reports smoke. After 'All safe' the alarm goes off again right away.`,"smoke.clear":`All safe`,"doorbell.section":`Doorbell`,"info.doorbell":`Choose this room's doorbell. For a UniFi Protect doorbell, the camera and screen of the same device are found automatically. RoomControl does nothing with the lamps when the doorbell rings.`,"doorbell.none":`No doorbell chosen`,"doorbell.off":`None`,"doorbell.entity":`Doorbell`,"doorbell.pick_hint":`Choose the doorbell (event or binary_sensor).`,"doorbell.last":`last rang`,"doorbell.never":`Not rung since the last restart`,"doorbell.camera":`Camera`,"doorbell.camera_hint":`A still image is added to the notification.`,"doorbell.no_camera":`None`,"doorbell.on_ring":`When it rings`,"doorbell.pause":`Pause media`,"doorbell.pause_hint":`Pause TV and music in rooms where someone is (motion in the last 10 minutes, or rooms without a motion sensor).`,"doorbell.announce":`Announce on speakers`,"doorbell.announce_hint":`The speakers of those rooms say someone is at the door (see Announcements in the general settings).`,"doorbell.announce_no_tts":`First choose a speech service under Announcements in the general settings.`,"doorbell.notify":`Notification`,"doorbell.notify_hint":`A Home Assistant notification (with camera image) and a roomcontrol_doorbell event, so you can make your own push message.`,"doorbell.quiet":`Quiet at night`,"doorbell.quiet_hint":`During these hours only the notification: no pausing or announcing.`,"doorbell.quiet_from":`Quiet from`,"doorbell.quiet_to":`Quiet until`,"doorbell.screen":`Doorbell screen`,"doorbell.screen_none":`This doorbell has no screen RoomControl can set.`,"doorbell.away_message":`Message when nobody is home`,"doorbell.away_message_hint":`While nobody is home the doorbell shows this message. When someone comes home, the previous message returns.`,"doorbell.pick_message":`Choose a message`,"doorbell.message_placeholder":`Parcel at the neighbours`,"bundles.auto_max":`Automatic brightness`,"bundles.auto_max_hint":`With motion and times the lamps go on at {pct}%, and the lux sensor never makes them brighter. By hand you can set them brighter; that stays until the lamp goes off.`,"bundles.auto_max_none":`No level chosen yet: the lamps go on at their own last brightness. Slide to choose a level.`,"bundles.sub_max":`{pct}%`,"bundles.restore":`Back to automatic brightness`,"debug.reason.brightness_by_hand":`brightness changed by hand`,"debug.reason.restore":`back to automatic`,"smoke.action_switches":`Devices off`,"smoke.action_switches_hint":`These switches go off right away, for example the espresso machine, a heater or the TV. At 'All safe' the switches that were on go on again.`,"smoke.switches_pick":`Choose a switch…`,"smoke.switches_add":`Another switch…`,"announce.section":`Announcements`,"announce.hint":`One message at once on the house's speakers. Smoke detectors, doorbell and your own automations use this. A room with linked persons (Presence) only takes part when one of them is home.`,"announce.tts":`Speech service`,"announce.tts_hint":`Speaks the messages on the media players.`,"announce.tts_none":`No speech service (tts.*) in Home Assistant: announcements don't work.`,"announce.tts_off":`None`,"announce.test":`Announce`,"announce.test_placeholder":`Dinner is ready`,"announce.sent":`Sent to {n} speaker(s).`,"announce.sent_none":`No speaker takes part now: nothing was sent.`,"announce.failed":`Sending failed.`,"announce.now_title":`Who gets a message now`,"announce.none":`No media players in the rooms yet. Add them under Media players in a room.`,"announce.status_on":`Takes part`,"announce.status_away":`Skipped`,"announce.status_off":`Doesn't take part`,"announce.why_off":`Switched off at the room's media players`,"announce.why_no_persons":`No persons linked: always takes part`,"announce.why_home":`Home: {names}`,"announce.why_away":`Not home: {names}`,"announce.service_hint":`In automations: action roomcontrol.announce with a message and optionally areas, or RoomControl's Announce notify entities.`,"announce.room_title":`Announcements`,"announce.room_no_persons":`No persons linked under Presence: these speakers always take part.`,"announce.room_persons_home":`Take part while one of these persons is home: {names}. Someone is home now.`,"announce.room_persons_away":`Take part while one of these persons is home: {names}. None of them is home now.`,"card.clock_next":`Alarm clock: {when}`,"card.clock_ringing":`Alarm clock is ringing`,"card.lock_locked":`Locked`,"card.lock_open":`Unlocked: {names}`,"card.lock_problem":`Lock problem: {names}`,"card.door_closed":`Door closed`,"card.door_open":`Door open: {names}`,"announce.save":`Save message`,"announce.use":`Use this message`,"texts.section":`Texts`,"texts.hint":`The texts RoomControl speaks or sends as a notification. Leave a field empty for the default text (grey). For spoken texts you choose the volume; 'Current' keeps the speakers at their own volume. After the message the volume goes back.`,"texts.reset":`Use the default text`,"texts.placeholders":`fills in:`,"texts.anomaly_motion":`Unusual motion`,"texts.anomaly_lights_on":`Lamps on long`,"texts.grp_smoke":`Texts on smoke`,"texts.grp_doorbell":`When the doorbell rings`,"texts.grp_alerts":`Notifications`,"texts.grp_announce":`Announcements (own messages)`,"texts.spoken":`Spoken`,"texts.notify":`Notification`,"texts.smoke_battery_short":`Low battery`,"texts.smoke_offline_short":`Unavailable`,"texts.volume":`Volume`,"texts.volume_own":`Current`,"texts.volume_clear":`Keep the speaker's own volume`,"texts.announce_note":`Test message, saved messages and roomcontrol.announce`,"debug.kind.lock":`lock`,"debug.kind.door":`door`,"debug.reason.door_open":`door opened`,"debug.reason.door_closed":`door closed`,"debug.reason.lock_state_locked":`locked`,"debug.reason.lock_state_unlocked":`unlocked`,"debug.reason.lock_state_open":`open`,"debug.reason.lock_state_jammed":`jammed`,"debug.reason.lock_state_unavailable":`unavailable`,"debug.reason.lock_state_unknown":`unknown`,"debug.reason.lock_time":`locked: lock time`,"debug.reason.lock_away":`locked: nobody home`,"debug.reason.lock_missed":`locked: missed lock time (restart)`,"debug.reason.lock_missed_found":`lock time missed during restart, catching up`,"debug.reason.lock_missed_gave_up":`missed lock time not caught up: lock stayed unavailable`,"debug.reason.lock_unavailable":`lock time, but the lock is unavailable`,"debug.reason.lock_already_locked":`lock time: already locked`,"debug.reason.lock_failed":`locking failed`,"debug.lock_at":`time`,"debug.now_locks":`Locks`,"debug.now_doors":`Doors`,"debug.since":`since`,"debug.lock_next":`next lock time`,"debug.lock_no_times":`no lock times on`,"debug.lock_away":`locks after {min} min nobody home`,"debug.lock_nobody_since":`nobody home since`,"debug.lock_catch_up":`waiting to catch up missed time:`,"debug.lock_state.locked":`Locked`,"debug.lock_state.unlocked":`Unlocked`,"debug.lock_state.open":`Open`,"debug.lock_state.jammed":`Jammed`,"debug.lock_state.locking":`Busy`,"debug.lock_state.unlocking":`Busy`,"debug.lock_state.unavailable":`Unavailable`,"debug.lock_state.unknown":`Unknown`,"debug.lock_state.missing":`Missing`,"debug.door_open":`Open`,"debug.door_closed":`Closed`,"fold.less":`Show less`,"fold.link_motion":`shares motion`,"fold.last":`last`,"fold.since":`since`,"fold.battery":`battery`,"fold.battery_low":`low`,"fold.unavailable":`Unavailable`,"door.none_hint":`No door sensors. A door that opens can switch lamps on, just like motion.`,"smart.show_more":`Show more`,"smart.show_less":`Show less`},nl:{"panel.title":`RoomControl`,"panel.version":`Versie van RoomControl`,"panel.loading":`Laden…`,"panel.load_error":`Kon de kamerconfiguratie niet laden.`,"panel.no_rooms":`Geen ruimtes gevonden.`,"panel.no_rooms_hint":`Maak ruimtes aan via Instellingen → Ruimtes, labels en zones.`,"room.back":`Terug`,"room.lights_section":`Lampen`,"room.lights_add":`Lamp toevoegen`,"room.lights_none":`Geen lampen toegewezen`,"room.motion_section":`Bewegingssensor`,"room.motion_none":`Geen bewegingssensoren`,"room.motion_pick":`Kies een bewegingssensor`,"room.dusk_section":`Aan als het donker wordt`,"room.dusk_hint":`Zet de lampen aan op het moment dat het donker wordt (de zon gaat onder). Wat toen aanging, blijft buiten het schema aan tot het weer licht is.`,"room.save":`Opslaan`,"room.saving":`Opslaan…`,"room.saved":`Opgeslagen`,"room.error_save":`Kon niet opslaan`,"card.on":`Aan`,"card.off":`Uit`,"card.motion":`Beweging`,"card.dusk":`Donker`,"card.lights":`lamp`,"card.lights_plural":`lampen`,"room.lux_section":`Luxsensoren`,"room.lux_pick":`Kies een lux- / verlichtingssensor`,"room.target_lux":`Doel-verlichtingssterkte (lux)`,"room.lux_hint":`Dimt of verheldert de lampen tot de ingestelde lux.`,"room.lux_now":`Huidig`,"room.lux_target":`Doel`,"settings.title":`Instellingen`,"common.close":`Sluiten`,"common.remove":`Verwijderen`,"common.retry":`Opnieuw`,"room.motion_clear":`Geen beweging`,"room.lux_none":`Geen luxsensor`,"room.sensor_add":`Sensor toevoegen`,"room.area_no_lights":`Geen andere lampen in deze ruimte. Wijs eerst lampen toe aan de ruimte in Home Assistant.`,"room.area_no_motion":`Geen bewegingssensoren in deze ruimte. Wijs er eerst een toe aan de ruimte in Home Assistant.`,"room.area_no_lux":`Geen luxsensoren in deze ruimte. Wijs er eerst een toe aan de ruimte in Home Assistant.`,"room.alarm_section":`Alarm`,"room.alarm_pick":`Kies een alarmpaneel`,"room.alarm_none":`Geen alarmpanelen gevonden in Home Assistant.`,"card.outside_schedule":`Buiten schema`,"room.schedules_section":`Schema's`,"room.schedules_add":`Schema toevoegen`,"room.schedules_none":`Geen schema's: de lampen mogen altijd aan.`,"room.schedules_pick":`Kies een schema`,"room.schedules_none_in_ha":`Geen schema's in Home Assistant. Maak er een via Instellingen → Apparaten & diensten → Helpers → Schema.`,"room.schedule_active":`actief`,"room.schedule_word":`schema`,"room.schedule_no_limit":`geen beperking`,"room.selector_section":`Actief schema gekozen door`,"room.selector_pick":`Kies een input_number`,"room.selector_none_in_ha":`Geen input_number-helpers in Home Assistant.`,"room.selector_hint":`Waarde 1 = eerste schema, 2 = tweede, enzovoort. 0 = geen beperking. Tijdens het actieve schema gaan de bundels die het schema volgen aan als het donker is. Buiten het schema zet alleen beweging het licht aan, uit na de grace period zonder beweging.`,"room.lights_select_all":`Alles selecteren`,"room.lights_add_selected":`Toevoegen`,"common.cancel":`Annuleren`,"panel.hidden_rooms":`Verborgen`,"panel.all_hidden":`Alle kamers zijn verborgen.`,"card.hide":`Verbergen`,"card.unhide":`Tonen`,"room.tab_settings":`Instellingen`,"room.tab_analysis":`Analyse`,"analysis.period":`Periode`,"analysis.period_24h":`24 uur`,"analysis.period_7d":`7 dagen`,"analysis.period_30d":`30 dagen`,"analysis.retention_note":`Home Assistant bewaart standaard 10 dagen geschiedenis (recorder purge_keep_days); oudere dagen tonen 0.`,"analysis.no_lights":`Voeg lampen toe aan deze kamer om het gebruik te zien.`,"analysis.load_error":`Kon de geschiedenis niet laden.`,"analysis.hour_short":`u`,"analysis.on_time":`Branduren`,"analysis.switched_on":`Keer aangezet`,"analysis.avg_per_day":`Gemiddeld per dag`,"analysis.on_without_motion":`Aan zonder beweging`,"analysis.detections":`detecties`,"analysis.no_motion_sensor":`Geen bewegingssensor ingesteld`,"analysis.chart_per_day":`Branduren per dag`,"analysis.chart_per_hour":`Minuten aan per uur`,"analysis.chart_profile":`Wanneer brandt het licht (gemiddelde minuten per uur van de dag)`,"analysis.minutes_on":`Minuten aan`,"analysis.avg_minutes_on":`Gem. minuten aan`,"analysis.show_table":`Als tabel tonen`,"analysis.per_lamp":`Per lamp`,"analysis.lamp":`Lamp`,"status.active":`Actief`,"status.standby":`Standby`,"overview.title":`Overzicht`,"person.home":`Thuis`,"person.away":`Afwezig`,"card.nobody_home":`Niemand thuis`,"settings.presence":`Aanwezigheid`,"settings.presence_hint":`Kies de personen die RoomControl volgt. Per kamer koppel je er een of meer: het licht daar werkt alleen als een van hen thuis is, en gaat uit als de laatste vertrekt.`,"settings.no_persons":`Geen personen in Home Assistant.`,"settings.display":`Weergave`,"settings.group_by_floor":`Kamers groeperen per etage`,"settings.group_by_floor_hint":`Gebruikt de etages uit Home Assistant (Instellingen → Ruimtes, labels en zones).`,"settings.no_floors":`Nog geen etages in Home Assistant. Voeg ze toe via Instellingen → Ruimtes, labels en zones.`,"floors.none":`Geen etage`,"room.presence_section":`Aanwezigheid`,"room.presence_no_persons":`Kies eerst personen in de instellingen van RoomControl (tandwiel op het dashboard).`,"room.presence_hint":`Met gekoppelde personen werkt het licht alleen als een van hen thuis is, en gaat het uit als de laatste vertrekt. Zonder gekoppelde personen telt aanwezigheid niet mee.`,"room.daylight_section":`Meekleuren met buitenlicht`,"room.daylight_title":`Kleur volgt de zon`,"room.daylight_hint":`Warm wit als de zon laag staat of onder is, koeler als hij hoog staat. Alleen de lampen die je hieronder aanvinkt.`,"room.daylight_now":`Nu`,"dim.to_1":`Dim aanzetten`,"dim.restore":`Terug naar vorige helderheid`,"dim.all_to_1":`Dim aanzetten in alle ingestelde kamers`,"dim.restore_all":`Helderheid in alle kamers terugzetten`,"dim.all_short":`Alles dim`,"dim.restore_all_short":`Alles terug`,"dim.error":`Kon de lampen niet dimmen.`,"room.motion_multi_hint":`Het licht gaat aan zodra één sensor beweging ziet, en pas uit als alle sensoren de hele grace period niets meer zien.`,"room.selector_required":`Verplicht bij meerdere schema's: kies het input_number dat het actieve schema kiest.`,"room.links_section":`Gekoppelde ruimten`,"room.links_add":`Ruimte koppelen`,"room.links_none":`Niet gekoppeld aan andere ruimten`,"room.links_none_available":`Geen andere ruimten om te koppelen.`,"room.links_hint":`Beweging in een gekoppelde ruimte zet hier het licht ook aan; het gaat pas uit als alle bewegingssensoren van alle gekoppelde ruimten de hele grace period niets zien. Koppelingen werken beide kanten op.`,"room.links_group":`Samen met`,"card.linked_with":`Gekoppeld met`,"room.daylight_lamps":`Lampen die meekleuren`,"room.daylight_not_capable":`Geen kleurtemperatuur`,"room.daylight_pick_required":`Kies minstens één lamp; tot die tijd kleurt er geen lamp mee.`,"room.daylight_no_lights":`Voeg eerst lampen toe aan deze kamer.`,"grace.label":`Grace period`,"grace.left":`nog`,"grace.setting":`Lampen blijven aan zonder beweging`,"grace.immediately":`uit zodra de beweging stopt`,"grace.setting_hint":`Max. 10 minuten. Geldt voor licht dat door beweging aanging, en voor gekoppelde ruimten.`,"grace.hint":`Geen beweging; het licht gaat uit als de grace period afloopt`,"analysis.avg_brightness":`Gem. helderheid`,"analysis.avg_lux":`Gem. lichtsterkte kamer`,"analysis.while_on":`terwijl het licht aan was`,"analysis.no_lux_sensor":`Geen luxsensor ingesteld`,"analysis.chart_brightness_day":`Helderheid waarop het licht brandde (gemiddeld per dag)`,"analysis.chart_brightness_hour":`Helderheid waarop het licht brandde (gemiddeld per uur)`,"analysis.chart_lux_day":`Lichtsterkte in de kamer terwijl het licht aan was (gemiddeld lux per dag)`,"analysis.chart_lux_hour":`Lichtsterkte in de kamer terwijl het licht aan was (gemiddeld lux per uur)`,"manual.title":`Handmatige controle`,"full_control.title":`Volledige controle door RoomControl`,"full_control.off_hint":`Uit: lampen en gordijnen reageren ook op schakelaars, andere apps en automatiseringen.`,"full_control.on_hint":`Aan: lampen en gordijnen volgen alleen RoomControl (automatisch, dit paneel en de RoomControl-entiteiten). Andere bediening wordt teruggezet. Tijdens handmatige controle kun je ze wel zelf bedienen.`,"manual.short":`Handmatig`,"manual.start":`Overnemen`,"manual.stop":`Teruggeven`,"manual.active":`RoomControl doet niets in deze kamer`,"manual.duration":`Duur van handmatige controle`,"manual.hint":`RoomControl doet hier de gekozen tijd niets automatisch en neemt het daarna weer over.`,"manual.error":`Kon handmatige controle niet wijzigen.`,"analysis.today":`Vandaag`,"analysis.now":`Nu`,"health.restart":`De RoomControl-backend die in Home Assistant draait ({running}) is ouder dan dit paneel ({expected}). Herstart Home Assistant (Instellingen → Systeem → Herstarten) zodat de nieuwe versie draait; tot die tijd gebruiken beweging, tijdvakken en de andere regels de oude code.`,"health.old":`ouder dan 1.1.0`,"health.inactive":`RoomControl heeft geen kamerlampen, dus niets reageert op beweging of tijdvakken. Controleer of RoomControl is toegevoegd onder Instellingen → Apparaten & diensten en zoek in het logboek naar “roomcontrol”.`,"motion_note.ignored":`Laatste beweging genegeerd`,"motion_note.manual":`handmatige controle is actief`,"motion_note.no_lights":`deze kamer heeft geen lampen`,"motion_note.already_on":`de lampen waren al aan`,"motion_note.nobody_home":`niemand die aan deze kamer gekoppeld is, is thuis`,"motion_note.slot":`er loopt een tijdvak: de bundels daarvan staan aan op hun niveau`,"debug.wants_on_slot":`hoort aan te staan (tijdvak loopt; dat wint van beweging)`,"motion_note.too_bright":`te licht ({lux} lx, donker vanaf {target} lx)`,"motion_note.outside_window":`sensor buiten zijn tijdvak`,"motion_window.label":`Zet licht aan van`,"motion_window.until":`tot`,"motion_window.always":`altijd`,"motion_window.clear":`Altijd`,"motion_window.hint":`Buiten dit tijdvak zet beweging de lampen niet aan; lampen die al aan zijn blijven aan zolang er beweging is. Leeg = altijd. Een tijdvak mag over middernacht lopen (bijv. 07:00 tot 01:00).`,"motion_note.no_entity":`RoomControl heeft nog geen lamp voor deze kamer, dus beweging doet hier niets. Herstart Home Assistant of controleer de RoomControl-integratie.`,"motion_note.not_tracked":`RoomControl volgt deze sensoren nog niet. Herstart Home Assistant als je RoomControl net hebt bijgewerkt.`,"fixed.pin":`Vastzetten op een vast dimlevel (reageert niet op de helderheidsschuif en de luxsensor)`,"fixed.unpin":`Vast dimlevel loslaten`,"fixed.label":`Vast niveau`,"fixed.slider_hint":`Vastgezette lampen houden hun vaste niveau`,"groups.section":`Groepen`,"groups.add":`Groep maken`,"groups.none":`Nog geen groepen. Elke groep wordt een eigen lamp bij het apparaat van de ruimte in Home Assistant (voor dashboards); een lamp kan in meer dan één groep zitten.`,"groups.no_lights":`Voeg eerst lampen toe aan deze kamer.`,"groups.default_name":`Groep`,"groups.name":`Naam van de groep`,"groups.empty":`Geen lampen in deze groep`,"groups.brightness":`Helderheid`,"groups.edit_lamps":`Lampen wijzigen`,"groups.pick_lamps":`Lampen in deze groep`,"door.section":`Deursensor`,"door.none":`Geen deursensoren`,"door.none_in_area":`Geen deursensoren in deze ruimte. Wijs er eerst een toe aan de ruimte in Home Assistant.`,"door.open":`Open`,"door.closed":`Dicht`,"door.turn_on_title":`Lampen aan als de deur opengaat`,"door.turn_on_hint_lux":`Alleen als het in de kamer donkerder is dan het lux-doel ({target} lx). Zonder verdere beweging gaan ze na de grace period uit.`,"door.turn_on_hint_nolux":`Zonder lux-doel telt het altijd als donker genoeg. Zonder verdere beweging gaan ze na de grace period uit.`,"door.groups":`Groepen die aangaan`,"door.no_groups":`Maak eerst een lampengroep in de sectie Groepen.`,"door.pick_group":`Kies minstens één groep; tot die tijd gaat er niets aan.`,"covers.section":`Gordijnen`,"covers.add":`Gordijn toevoegen`,"covers.none":`Geen gordijnen`,"covers.none_in_area":`Geen gordijnen of screens in deze ruimte. Wijs ze eerst toe aan de ruimte in Home Assistant.`,"covers.groups":`Gordijngroepen`,"covers.groups_none":`Nog geen groepen. Groepeer gordijnen om ze samen te openen en te sluiten, of laat ze donker/licht volgen.`,"covers.group_empty":`Geen gordijnen in deze groep`,"covers.open":`Open`,"covers.stop":`Stop`,"covers.close":`Dicht`,"covers.edit":`Gordijnen wijzigen`,"covers.pick":`Gordijnen in deze groep`,"covers.follow_title":`Volgt donker/licht`,"covers.follow_hint":`Dicht bij schemer of donker, open bij zonsopkomst of op een vaste tijd (zie hieronder). Tussendoor kun je ze zelf bedienen.`,"covers.follow_hint_noschedule":`Deze kamer heeft geen schema: de gordijnen gaan dicht als het donker wordt en gaan alleen vanzelf open met 'Open bij'.`,"covers.state_open":`Open`,"covers.state_closed":`Dicht`,"covers.state_opening":`Gaat open`,"covers.state_closing":`Gaat dicht`,"fan.section":`Ventilator`,"fan.add":`Ventilator toevoegen`,"fan.none":`Geen ventilator`,"fan.none_in_area":`Geen ventilatoren in deze ruimte. Wijs er eerst een toe aan de ruimte in Home Assistant.`,"fan.steps":`Snelheid bij activiteit`,"fan.steps_none":`Nog geen stappen: de ventilator wordt niet aangestuurd.`,"fan.after":`Na`,"fan.minutes":`min`,"fan.speed":`Snelheid`,"fan.add_step":`Stap toevoegen`,"fan.active_since":`Activiteit sinds`,"fan.idle":`Geen activiteit`,"fan.needs_motion":`Voeg een bewegingssensor toe aan deze kamer: activiteit wordt met beweging gemeten.`,"fan.hint":`Activiteit begint bij de eerste beweging en loopt door zolang er beweging is, plus de nadraaitijd. Bij elke stap gaat de ventilator harder; als de activiteit stopt, gaat de ventilator uit.`,"fan.temp_title":`Aan bij temperatuur`,"fan.temp_off":`Uit: de ventilator gaat alleen aan bij activiteit.`,"fan.temp_hint":`Vanaf deze temperatuur draait de ventilator, ook zonder beweging.`,"fan.temp_pick":`Kies een temperatuursensor`,"fan.temp_none":`Geen temperatuursensoren in deze ruimte. Wijs er eerst een toe aan de ruimte in Home Assistant.`,"fan.temp_from":`Vanaf`,"fan.temp_active":`Nu {temp}: ventilator draait door de temperatuur.`,"fan.temp_inactive":`Nu {temp}: onder de grens.`,"fan.run_on_title":`Eigen nadraaitijd na de laatste beweging`,"fan.run_on_hint":`Zo lang blijft de ventilator draaien nadat er geen beweging meer is.`,"fan.run_on_default":`Uit: de ventilator draait na zolang de grace period duurt ({time}).`,"fan.run_on_until":`Ventilator gaat uit om`,"fan.shared_via":`gedeeld via {room}`,"fan.share_title":`Delen met`,"fan.share_add":`Ruimte`,"fan.share_none":`Gebruiken twee soortgelijke ruimten (bijv. WC BG en WC 1ste) één ventilator? Deel hem dan.`,"fan.share_hint":`De ruimten die een ventilator delen hebben samen één activiteit: die begint bij de eerste beweging in een van de ruimten en de stappen lopen door zolang er in minstens één ruimte beweging is. Pas als in geen enkele ruimte nog beweging is, start de nadraaitijd; daarna gaat de ventilator uit. Delen werkt beide kanten op.`,"fan.steps_shared":`Geen eigen stappen: de stappen van {room} worden gebruikt ({steps}).`,"alarm.motion_only_no_sensor":`Deze kamer heeft geen bewegingssensor: lampen die aangaan, gaan na de grace period weer uit.`,"alarm.motion_only_active":`Nu actief: de lampen reageren alleen op beweging.`,"alarm.pick_required":`Kies het alarmpaneel; tot die tijd doen deze opties niets.`,"alarm.last_off":`Alarm zette de lampen het laatst uit:`,"alarm.never_off":`Het alarm heeft de lampen nog niet uitgezet (sinds de laatste herstart).`,"alarm_state.disarmed":`Uitgeschakeld`,"alarm_state.armed_home":`Armed Home`,"alarm_state.armed_away":`Armed Away`,"alarm_state.armed_night":`Armed Night`,"alarm_state.armed_vacation":`Armed Vacation`,"alarm_state.arming":`Inschakelen…`,"alarm_state.pending":`Wachten…`,"alarm_state.triggered":`Alarm!`,"settings.alarm":`Alarm`,"settings.alarm_hint":`Het alarmpaneel voor het hele huis. Kamers zonder eigen alarmpaneel gebruiken dit paneel.`,"settings.alarm_panel":`Alarmpaneel`,"settings.alarm_none":`Geen`,"settings.dim_armed_home":`Dim bij Armed Home (alle kamers)`,"settings.dim_armed_home_hint":`Zolang het alarm op Armed Home staat, staan alle kamers op Dim; per kamer kun je dit overrulen.`,"settings.dim_armed_home_needs_alarm":`Kies eerst het alarmpaneel.`,"alarm.dim_title":`Dim bij Armed Home`,"alarm.dim_default":`Algemeen ({state})`,"alarm.dim_on":`Altijd`,"alarm.dim_off":`Nooit`,"alarm.dim_state_on":`aan`,"alarm.dim_state_off":`uit`,"alarm.dim_default_tip":`Volg de algemene instelling 'Dim bij Armed Home (alle kamers)'`,"alarm.dim_on_tip":`Deze kamer dimt altijd bij Armed Home, wat de algemene instelling ook is`,"alarm.dim_off_tip":`Deze kamer dimt nooit bij Armed Home, wat de algemene instelling ook is`,"alarm.now":`Nu`,"alarm.panel_general":`uit de algemene instellingen`,"alarm.panel_own":`eigen keuze voor deze kamer`,"alarm.panel_none":`Nog geen alarmpaneel gekozen`,"alarm.panel_pick_other":`Ander paneel kiezen`,"alarm.panel_use_general":`Algemeen paneel gebruiken`,"alarm.panel_remove":`Paneel weghalen`,"alarm.opt_none":`Niets`,"alarm.opt_none_hint":`Lampen werken gewoon zoals altijd`,"alarm.opt_off":`Alles uit`,"alarm.opt_off_hint":`Uit zodra deze stand begint`,"alarm.opt_motion":`Alleen beweging`,"alarm.opt_motion_hint":`Alleen aan bij beweging, uit na de grace period`,"alarm.both_old":`Deze kamer had 'Uit bij Armed Home' én 'Alleen beweging' aan; dat blijft zo tot je hier een keuze maakt.`,"alarm.dim_also":`En gedimd branden`,"alarm.dim_default_card":`Volg de instelling voor alle kamers`,"alarm.dim_on_card":`Lampen branden gedimd in deze stand`,"alarm.dim_off_card":`Lampen branden op hun gewone niveau`,"lux.dark_title":`Donker vanaf`,"lux.mode_title":`Sensoren combineren`,"lux.combined":`Gecombineerd`,"lux.mode_average":`Gemiddelde`,"lux.mode_min":`Laagste`,"lux.mode_max":`Hoogste`,"lux.mode_median":`Mediaan`,"lux.mode_sum":`Opgeteld`,"lux.mode_average_hint":`Het gemiddelde van alle sensoren telt.`,"lux.mode_min_hint":`De donkerste sensor telt: de ruimte is donker zodra één plek donker is.`,"lux.mode_max_hint":`De lichtste sensor telt: de ruimte is pas donker als het overal donker is.`,"lux.mode_median_hint":`De middelste waarde telt; één afwijkende sensor (bijv. in de zon) telt nauwelijks mee.`,"lux.mode_sum_hint":`Alle sensorwaarden worden opgeteld. Stel de drempels en doel-lux daarop af.`,"lux.always":`altijd`,"lux.dark_hint":`Onder {lux} lx is deze ruimte donker: alleen dan zetten beweging en de deursensor het licht aan.`,"lux.dark_hint_always":`0 = de ruimte telt altijd als donker.`,"lux.is_dark":`donker`,"lux.is_light":`licht genoeg`,"lux.control_title":`Verlichten tot doel-lux`,"lux.control_hint":`Zolang het buiten licht is, controleert RoomControl continu de lux en dimt of versterkt de lampen (niet de vastgezette) in kleine stappen tot het doel bereikt is. Is het donker, dan geldt de standaard helderheid.`,"lux.default_title":`Standaard helderheid`,"lux.not_set":`niet ingesteld`,"lux.default_hint":`Lampen die RoomControl aanzet, gaan naar dit niveau. Is het donker (zon onder), dan geldt dit in plaats van de luxregeling; lampen die branden gaan dan naar dit niveau.`,"daylight.rgb_title":`Kleurlampen kleuren mee (RGB)`,"daylight.rgb_hint":`Lampen die kleur kunnen, krijgen de kleur van de zon als RGB (zoals prefer_rgb_color van Adaptive Lighting); andere lampen krijgen een kleurtemperatuur binnen hun eigen bereik.`,"daylight.rgb_none":`Geen van de lampen in deze kamer kan kleur.`,"daylight.warmest":`Warmst`,"daylight.coolest":`Koelst`,"groups.schedule_keys":`Schemagegevens voor Dim:`,"groups.or":`of`,"dim.button":`Dim`,"ha_name.label":`Naam in Home Assistant`,"ha_name.hint":`Verschijnt bij het apparaat van de ruimte als`,"ha_name.covers_default":`Gordijnen`,"ha_name.fans_default":`Ventilator`,"bundles.add":`Bundel maken`,"bundles.default_name":`Bundel`,"bundles.none":`Nog geen lampen. Kies 'Bundel maken' en selecteer een of meer lampen: die worden samen een bundel, met eigen instellingen en een eigen lamp in Home Assistant.`,"bundles.pick":`Selecteer de lampen voor de nieuwe bundel`,"bundles.no_free":`Alle lampen van deze ruimte zitten al in een bundel (of de ruimte heeft geen lampen in Home Assistant).`,"bundles.settings":`Instellingen van deze bundel`,"bundles.expand":`Bundel openklappen`,"bundles.collapse":`Bundel inklappen`,"bundles.brightness":`Helderheid`,"bundles.mode_default":`Standaard`,"bundles.mode_fixed":`Vast`,"bundles.default_hint":`Met de schuif hierboven kies je de helderheid voor beweging en tijden. Kies Vast om de lampen altijd op één niveau te houden.`,"bundles.default_level":`Deze bundel heeft nog een eigen standaardniveau van {pct}%.`,"bundles.default_level_clear":`Wissen`,"bundles.fixed_hint":`Altijd dit niveau: reageert niet op de helderheidsschuif en de luxsensor.`,"bundles.daylight_on":`Kleur volgt de zon`,"bundles.when_on":`Wanneer aan`,"bundles.on_motion":`Bij beweging`,"bundles.no_motion_sensor":`Deze ruimte heeft nog geen bewegingssensor.`,"bundles.on_door":`Als de deur opengaat (en het donker is)`,"bundles.no_door_sensor":`Deze ruimte heeft nog geen deursensor.`,"bundles.on_dusk":`Als het donker wordt`,"bundles.on_dusk_hint":`Aan op het moment dat de zon ondergaat.`,"bundles.follow_schedule":`Volgt het schema`,"bundles.follow_schedule_hint":`Buiten het actieve schema niet aan, en uit als het schema eindigt. Uit = deze bundel mag altijd aan.`,"bundles.dim_lux":`Dim en lux`,"bundles.dim":`Doet mee met Dim`,"bundles.dim_hint":`Bij de Dim-knop, Dim bij Armed Home en 'Dim vanaf' in een tijdvak.`,"bundles.lux":`Verlichten tot doel-lux`,"bundles.lux_hint":`Overdag stuurt RoomControl deze lampen bij tot {target} lx.`,"bundles.lux_target_off":`De doel-lux staat uit voor deze ruimte.`,"bundles.no_lux_sensor":`Voeg eerst een luxsensor toe aan deze ruimte.`,"bundles.delete":`Bundel verwijderen`,"door.per_bundle":`Welke lampen aangaan als de deur opengaat, stel je per bundel in bij Lampen (Wanneer aan → deur).`,"lux.target_title":`Doel-lux (voor bundels met luxregeling)`,"lux.target_on_hint":`Overdag sturen bundels met luxregeling hun lampen bij tot deze waarde.`,"lux.target_off_hint":`Uit: geen luxregeling in deze ruimte, ook niet voor bundels waar die aan staat.`,"room.schedules_none_in_area":`Geen schema's in deze ruimte. Maak een schema via Instellingen → Apparaten & diensten → Helpers → Schema, en kies bij de instellingen van dat schema deze ruimte.`,"room.selector_none_in_area":`Geen input_number in deze ruimte. Maak er een via Instellingen → Apparaten & diensten → Helpers → Getal, en kies bij de instellingen ervan deze ruimte.`,"alarm.question_state":`Als het alarm naar {state} gaat`,"alarm.opt_on":`Alles aan`,"alarm.opt_on_hint":`Aan zodra deze stand begint, als het donker is`,"alarm.dim_yes":`Ja`,"alarm.dim_no":`Nee`,"alarm.dim_short":`gedimd`,"alarm.sum_none":`Samengevat: bij {state} verandert het alarm hier niets aan de lampen.`,"alarm.sum_none_dim":`Samengevat: bij {state} branden de lampen hier gedimd; verder verandert er niets.`,"alarm.sum_off":`Samengevat: bij {state} gaan de lampen hier uit.`,"alarm.sum_off_dim":`Samengevat: bij {state} gaan de lampen hier uit; gaan ze weer aan, dan branden ze gedimd.`,"alarm.sum_on":`Samengevat: bij {state} gaan de lampen hier aan als het donker is.`,"alarm.sum_on_dim":`Samengevat: bij {state} gaan de lampen hier gedimd aan als het donker is.`,"alarm.sum_motion":`Samengevat: bij {state} gaan de lampen hier alleen aan bij beweging.`,"alarm.sum_motion_dim":`Samengevat: bij {state} gaan de lampen hier alleen aan bij beweging, en dan gedimd.`,"fan.change":`Wijzigen`,"fan.when":`Wanneer gaat de ventilator aan?`,"fan.trigger_motion":`Bij beweging`,"fan.trigger_motion_hint":`Sneller naarmate het langer duurt`,"fan.trigger_temp":`Bij temperatuur`,"fan.trigger_temp_hint":`Vanaf een ingestelde temperatuur`,"fan.trigger_manual":`Alleen handmatig`,"fan.trigger_manual_hint":`RoomControl stuurt de ventilator niet`,"fan.steps_title":`Bij beweging: snelheid per stap`,"fan.reason_activity":`activiteit`,"fan.reason_temp":`temperatuur`,"fan.run_on_how_long":`Hoe lang nadraaien`,"fan.run_on_grace":`Grace period`,"fan.run_on_own":`Eigen tijd`,"fan.run_on_own_hint":`Zelf kiezen`,"fan.sum_prefix":`Samengevat: de ventilator draait`,"fan.sum_motion":`bij beweging (van {from} naar {to})`,"fan.sum_temp":`vanaf {lo} graden op {speed}`,"fan.sum_and":`, en `,"fan.sum_highest":`; de hoogste snelheid telt.`,"fan.sum_run_on":`Nadraaien: {time}.`,"fan.sum_manual":`Samengevat: RoomControl stuurt de ventilator niet; je bedient hem zelf.`,"fan.level_low":`Laag`,"fan.level_medium":`Medium`,"fan.level_high":`Hoog`,"fan.nobody_home":`Niemand thuis: de ventilator blijft uit.`,"fan.presence_rule":`Is er niemand thuis, dan blijft de ventilator uit.`,"fan.expand":`Ventilatorinstellingen openklappen`,"fan.status_label":`Ventilator`,"fan.status_off":`uit`,"fan.status_step":`stap {n} van {total}`,"fan.status_until":`uit om`,"fold.expand":`Openklappen`,"fold.schedules":`{n} schema('s) · nu actief: {active}`,"fold.none_active":`geen`,"fold.presence_none_enabled":`Nog geen personen gekozen in de instellingen`,"fold.presence_none":`Geen personen gekoppeld: aanwezigheid speelt geen rol`,"fold.home":`thuis`,"fold.away":`weg`,"fold.motion":`{n} sensor(en) · {state}`,"fold.lux":`{n} sensor(en) · nu {lux}`,"fold.covers":`{n} gordijn(en) · {follow}`,"fold.covers_follow":`volgen donker/licht`,"fold.covers_manual":`alleen met de hand`,"lux.sensor_chip":`Sensor`,"lux.mode_question":`Hoe tellen de sensoren mee?`,"lux.target_off_title":`Uit`,"lux.target_off_card":`Geen luxregeling`,"lux.target_on_title":`Aan`,"lux.target_on_card":`Overdag bijsturen`,"lux.sum_now_light":`Samengevat: {how} {lux} lx, dus licht genoeg.`,"lux.sum_now_dark":`Samengevat: {how} {lux} lx, dus donker.`,"lux.sum_single":`nu`,"lux.sum_dark":`Donker vanaf {lux} lx.`,"lux.sum_always_dark":`De ruimte telt altijd als donker.`,"lux.sum_target":`Overdag sturen bundels met luxregeling bij tot {lux} lx.`,"lux.sum_target_off":`Geen luxregeling.`,"lux.alarm_pause_title":`Niet bijsturen bij alarmstand`,"lux.alarm_pause_none":`Geen stand gekozen: de luxregeling werkt in elke alarmstand.`,"lux.alarm_pause_hint":`Bij {states} stuurt RoomControl de lampen hier niet bij.`,"lux.alarm_pause_no_panel":`Kies eerst een alarmpaneel (bij Alarm of in de instellingen); tot die tijd doet dit niets.`,"lux.alarm_paused_now":`Nu gepauzeerd door de alarmstand.`,"lux.sum_alarm_pause":`Niet bij {states}.`,"fold.selector_missing":`input_number ontbreekt (verplicht)`,"info.show":`Uitleg tonen`,"info.hide":`Uitleg verbergen`,"info.lights":`Lampen zitten in bundels. Een bundel is één of meer lampen die samen dezelfde instellingen krijgen: hoe fel ze aangaan, of ze het daglicht volgen, en wanneer ze aangaan (bij beweging, de deur, of in hun eigen tijdvakken). Elke bundel wordt ook een eigen lamp in Home Assistant.`,"info.schedules":`Een schema (helper in Home Assistant) bepaalt wanneer het licht hier aan hoort. Zolang het schema aan is, staan de bundels die het schema volgen aan op hun niveau; overdag sturen bundels met luxregeling naar de doel-lux. Buiten het schema gaat het licht aan bij beweging: als de zon onder is, of overdag als het donkerder is dan 'Donker vanaf'. Met twee of meer schema's kies je met een input_number welk schema geldt (1 = eerste, 0 = geen beperking).`,"info.links":`Gekoppelde ruimten delen hun beweging: beweging in de ene ruimte houdt ook het licht in de andere aan. Handig voor een open keuken met woonkamer of een hal met overloop. Koppelingen werken beide kanten op.`,"info.presence":`Kies welke personen bij deze ruimte horen. Is geen van hen thuis, dan gaat het licht hier niet automatisch aan. Zonder gekoppelde personen speelt aanwezigheid geen rol.`,"info.motion":`Bewegingssensoren zetten het licht aan als het donker is, en uit na de grace period zonder beweging. Met meerdere sensoren telt beweging op één ervan. De grace period stel je hier ook in.`,"info.doors":`Een deursensor zet het licht aan zodra de deur opengaat en het donker is, zoals bij beweging. Per bundel kies je of die op de deur reageert.`,"info.alarm":`Bij Uitgeschakeld volgen de lampen tijdvakken, zon en beweging. Bij Armed Home gaan ze uit, behalve waar beweging is (op Dim). Bij Armed Away (niemand thuis) gaan ze uit, tenzij je voor deze ruimte 'Niet uitzetten, tijdvak volgen' kiest: dan volgen de lampen het tijdvak van de bundel en gaan uit als dat afloopt.`,"info.lux":`Luxsensoren meten hoe licht het is. 'Donker vanaf' bepaalt wanneer beweging en de deur het licht aanzetten. Met de doel-lux sturen bundels met luxregeling overdag hun lampen bij tot die waarde. Bij meerdere sensoren kies je hoe ze meetellen.`,"info.fan":`De ventilator kan aangaan bij beweging (sneller naarmate het langer duurt), vanaf een temperatuur, of alleen met de hand. Na de laatste beweging draait hij nog even na. Is er niemand thuis, dan blijft hij uit. Twee ruimten kunnen één ventilator delen.`,"info.covers":`Voeg de gordijnen of screens van deze ruimte toe. Open, Stop en Dicht bedienen ze allemaal tegelijk. Met 'Volgt donker/licht' gaan ze dicht bij schemer of donker, en open bij zonsopkomst of op een vaste tijd.`,"bundles.t_motion":`Beweging`,"bundles.t_door":`Deur`,"bundles.t_dusk":`Donker`,"bundles.t_schedule":`Schema`,"bundles.when_question":`Wanneer gaan deze lampen aan?`,"bundles.when_info":`Met eigen tijden wint het tijdvak: zolang een tijdvak loopt, staat de bundel aan op zijn niveau (overdag met luxregeling: de doel-lux). Buiten de tijdvakken zetten beweging en de deur de bundel aan als de zon onder is, of overdag als het donkerder is dan 'Donker vanaf'.`,"bundles.one_lamp":`1 lamp`,"bundles.n_lamps":`{n} lampen`,"bundles.lamp_chip":`Lamp`,"bundles.sub_by_hand":`alleen met de hand`,"bundles.sub_daylight":`daglicht`,"bundles.sub_fixed":`vast {pct}%`,"bundles.sub_default":`standaard`,"bundles.mode_default_card":`Eigen niveau van de lamp`,"bundles.mode_fixed_card":`Altijd dit niveau`,"bundles.colour":`Kleur`,"bundles.colour_own":`Eigen kleur`,"bundles.colour_own_card":`De lamp kiest zelf`,"bundles.extra":`Extra`,"bundles.extra_dim":`Doet mee met Dim`,"bundles.extra_lux":`Luxregeling`,"bundles.sum_when":`Samengevat: {name} gaat aan bij {when}.`,"bundles.sum_fixed":`Altijd op {pct}%,`,"bundles.sum_default":`Op het eigen niveau,`,"bundles.sum_daylight":`in de kleur van het daglicht.`,"bundles.sum_own_colour":`in de eigen kleur.`,"bundles.sum_dim":`Doet mee met Dim.`,"bundles.sum_lux":`Wordt overdag bijgestuurd op lux.`,"info.dim_codes_title":`Dimmen via het schema:`,"info.dim_codes_where":`open in de schema-helper een tijdblok, kies 'Meer opties' en zet daar een of meer van deze regels. Zolang dat blok actief is, staan die lampen op Dim.`,"info.dim_code_all":`alle bundels die meedoen met Dim`,"info.dim_code_bundle_name":`bundel {name}`,"ha_name.label_lights":`Naam van licht die hele ruimte bedient`,"overview.lit":`Licht brandt in {n} van {total} ruimten`,"overview.n_links":`{n} koppeling(en)`,"overview.none_on":`Nergens brandt licht`,"overview.linked":`Gekoppeld`,"overview.kind_motion":`Beweging`,"overview.kind_fan":`Ventilator`,"overview.kind_motion_hint":`beweging in de ene ruimte houdt het licht in de andere aan`,"overview.kind_fan_hint":`één ventilator voor deze ruimten`,"overview.edge_motion":`direct`,"overview.edge_fan":`deelt`,"overview.n_on":`licht aan in {n}`,"overview.via":`{a} en {b} via {through}`,"settings.alarm_fixed":`Uitgeschakeld: de lampen volgen tijdvakken, zon en beweging. Armed Home: de lampen gaan uit, behalve waar beweging is (op Dim), uit na de grace period. Armed Away: alle lampen uit, behalve in ruimten die bij niemand thuis niet uitgezet worden; die volgen het tijdvak van de bundel.`,"settings.sun":`Zon`,"settings.sun_hint":`Deze zon-entiteit bepaalt voor alle ruimten of de zon onder is.`,"settings.sun_entity":`Zon-entiteit`,"settings.sun_down":`Nu: zon onder`,"settings.sun_up":`Nu: zon op`,"settings.sun_missing":`Niet gevonden: voeg de integratie Zon toe in Home Assistant.`,"bundles.evening_hint":`Als een tijdvak loopt en de zon onder is, brandt de bundel op dit niveau.`,"alarm.fixed_disarmed":`De lampen volgen tijdvakken, zon en beweging zoals ingesteld.`,"alarm.fixed_home":`De lampen gaan uit, behalve waar er nog beweging is. Bij beweging aan op Dim, uit na de grace period.`,"alarm.fixed_away":`De lampen gaan uit en blijven uit zolang niemand thuis is.`,"alarm.fixed_other":`Deze alarmstand verandert niets aan de lampen.`,"motion_note.armed_away":`het alarm staat op Armed Away`,"motion_note.lux_control":`het schema is aan: de doel-lux stuurt de lampen`,"motion_note.sun_up":`de zon is op en het is niet donker genoeg`,"card.bundle":`bundel`,"card.bundles":`bundels`,"card.sun_down":`Donker: de zon is onder`,"card.sun_up":`Licht`,"card.link_motion":`Koppeling {n}: beweging gedeeld`,"card.link_fan":`Koppeling {n}: ventilator gedeeld`,"clock.section":`Wekkers`,"clock.add":`Wekker`,"clock.none":`Nog geen wekkers`,"clock.default_name":`Wekker`,"clock.time":`Tijd`,"clock.name":`Naam`,"clock.days":`Dagen (elke week)`,"clock.day_0":`ma`,"clock.day_1":`di`,"clock.day_2":`wo`,"clock.day_3":`do`,"clock.day_4":`vr`,"clock.day_5":`za`,"clock.day_6":`zo`,"clock.once":`Eenmalig`,"clock.every_day":`elke dag`,"clock.no_days":`geen dagen`,"clock.days_hint":`De wekker herhaalt elke week op de gekozen dagen. Eenmalig: hij gaat één keer af en zet zichzelf daarna uit.`,"clock.persons":`Alleen als thuis`,"clock.persons_none":`Kies eerst personen voor wekkers in de instellingen (vinkje 'Wekker'); tot die tijd gaat de wekker altijd af.`,"clock.persons_chosen":`De wekker gaat alleen af als minstens één van deze personen thuis is.`,"clock.persons_room":`Niets gekozen: de personen van de ruimte tellen ({names}).`,"clock.persons_anyone":`Niets gekozen en geen personen bij de ruimte: de wekker gaat altijd af.`,"clock.bundles":`Bundels`,"clock.no_bundles":`geen bundels`,"clock.snooze":`Stapsgewijs`,"clock.snooze_on":`Stapsgewijs aan`,"clock.snooze_off_hint":`Uit: op de ingestelde tijd gaan de lampen direct aan op 100%.`,"clock.snooze_on_hint":`Aan: het licht begint zacht en wordt elke interval een stap feller.`,"clock.sub_snooze":`stapsgewijs {n}×`,"clock.snoozes":`Aantal stappen`,"clock.snooze_minutes":`Interval`,"clock.snooze_n":`stap {n}`,"clock.snooze_hint":`Het gaat vanzelf in gelijke stappen naar 100%: elke interval een stap verder. Je hoeft nergens op te drukken. Met de stopknop van de wekker zet je hem uit.`,"clock.music_title":`Muziek`,"clock.music":`muziek`,"clock.no_music":`geen muziek`,"clock.no_players":`Geen mediaspeler in deze ruimte en geen Music Assistant-speler zonder ruimte. Wijs een speler toe aan de ruimte in Home Assistant.`,"clock.player":`Mediaspeler`,"clock.media":`Wat speelt er`,"clock.media_chosen":`Gekozen`,"clock.ha_hint":`In Home Assistant staan onder het apparaat van de ruimte per wekker een knop 'stoppen' en een aan/uit-schakelaar.`,"clock.summary":`Samengevat: {days} om {time} gaan {bundles} aan op {first}%, daarna in {n} stap(pen) van {min} min tot 100%.`,"clock.summary_direct":`Samengevat: {days} om {time} gaan {bundles} direct aan op 100%.`,"clock.summary_music":`Muziek op {player}, met elke stap harder.`,"clock.summary_stop":`Zonder reactie bij de stopstap om {time}: {what}.`,"clock.delete":`Wekker verwijderen`,"info.clocks":`Een wekker zet op de gekozen dagen en tijd de gekozen bundels aan, eventueel met muziek en gordijnen die opengaan. Zonder 'Stapsgewijs' direct op 100%; met 'Stapsgewijs' elke interval een stap verder tot 100%. De wekker gaat alleen af als iemand van de gekozen personen thuis is.`,"clock.music_on":`Muziek aan`,"clock.music_off_hint":`Uit: de wekker zet alleen het licht aan.`,"clock.music_on_hint":`Aan: muziek op de gekozen speler, met elke stap harder.`,"clock.music_pick":`Kies een speler en wat er speelt.`,"clock.pick_player":`Kies een speler…`,"debug.title":`Debuglog`,"debug.sub":`Waarom bundels wel of niet aan/uit gaan · nieuwste bovenaan · ververst elke 3 s`,"debug.empty":`Nog niets gelogd sinds de laatste herstart.`,"debug.kind.on":`Aan`,"debug.kind.off":`Uit`,"debug.kind.adjust":`Bijgestuurd`,"debug.kind.ignored":`Genegeerd`,"debug.kind.blocked":`Niet aan`,"debug.kind.info":`Info`,"debug.reason.motion":`beweging`,"debug.reason.door":`deur open`,"debug.reason.schedule_sun_down":`schema aan, zon onder`,"debug.reason.alarm_off_schedule_sun_down":`alarm uit, schema aan, zon onder`,"debug.reason.schedule_ended":`schema afgelopen`,"debug.reason.nobody_home":`niemand thuis`,"debug.reason.no_motion":`geen beweging (grace period voorbij)`,"debug.reason.alarm_armed_home":`alarm Armed Home`,"debug.reason.alarm_armed_away":`alarm Armed Away`,"debug.reason.lux_dark":`te donker voor de doel-lux`,"debug.reason.lux_bright":`te licht, lampen hebben geen effect`,"debug.reason.lux_brighter":`feller naar de doel-lux`,"debug.reason.lux_dimmer":`zachter naar de doel-lux`,"debug.reason.alarm_clock":`wekker`,"debug.reason.manual_start":`handmatige controle gestart`,"debug.reason.manual_end":`handmatige controle afgelopen`,"debug.reason.manual_control_ended_lights_not_allowed_now":`handmatig afgelopen: licht mag nu niet`,"debug.reason.manual_control_ended_motion":`handmatig afgelopen: beweging`,"debug.reason.external_on":`aangezet buiten RoomControl om (schakelaar, app, automatisering)`,"debug.reason.conditions":`omstandigheden veranderd`,"debug.why.manual":`handmatige controle is actief`,"debug.why.armed_home":`alarm staat op Armed Home (alleen beweging)`,"debug.why.armed_away":`alarm staat op Armed Away`,"debug.why.nobody_home":`niemand thuis`,"debug.why.schedule":`schema staat het niet toe`,"debug.target":`doel`,"debug.clock":`wekker`,"debug.schedule":`schema`,"debug.sun":`zon`,"debug.home":`iemand thuis`,"debug.v_on":`aan`,"debug.v_off":`uit`,"debug.v_down":`onder`,"debug.v_up":`op`,"debug.v_yes":`ja`,"debug.v_no":`nee`,"debug.now":`Nu`,"debug.now_schedule":`Schema`,"debug.now_no_schedule":`geen (telt als schema uit)`,"debug.now_sun":`Zon`,"debug.now_missing":`niet gevonden`,"debug.now_alarm":`Alarm`,"debug.now_home":`Iemand thuis`,"debug.now_manual":`Handmatig`,"debug.now_motion":`Beweging nu`,"debug.now_lux":`Lux`,"debug.now_dark_from":`donker vanaf`,"debug.now_bundles":`Per bundel: wat RoomControl nu wil`,"debug.alarm_normal":`uitgeschakeld / geen`,"debug.alarm_home":`Armed Home`,"debug.alarm_away":`Armed Away`,"debug.wants_lux":`luxregeling stuurt (aan als het te donker is)`,"debug.wants_motion":`gaat aan bij beweging`,"debug.wants_off_schedule":`blijft uit (schema uit, zon op)`,"debug.wants_off_away":`blijft uit (Armed Away)`,"debug.wants_motion_1pct":`alleen bij beweging, op Dim (Armed Home)`,"debug.wants_nothing":`niets automatisch (bv. te licht, of bundel volgt beweging niet)`,"debug.flag_schedule":`volgt schema`,"debug.flag_no_schedule":`volgt schema niet`,"debug.flag_motion":`beweging`,"debug.flag_lux":`luxregeling`,"motion_note.schedule":`het schema is aan: bundels die het schema volgen, staan aan op hun niveau`,"debug.wants_on_schedule":`hoort aan te staan (schema aan; het schema wint van beweging)`,"debug.reason.schedule":`schema aan`,"alarm.fixed_away_ignored":`Deze ruimte wordt niet uitgezet als er niemand thuis is. De lampen volgen het tijdvak van de bundel en gaan uit als dat afloopt.`,"bundles.move_up":`Omhoog`,"bundles.move_down":`Omlaag`,"analysis.period_3d":`3 dagen`,"analysis.period_max":`{n} dagen (max)`,"analysis.kept":`Home Assistant bewaart {n} dagen`,"analysis.light_on":`licht aan`,"analysis.schedule_on":`schema aan`,"analysis.on_in_schedule":`van schematijd aan`,"analysis.on_outside":`aan buiten schema`,"analysis.lg_schedule":`Schema`,"analysis.lg_sun":`zon onder`,"analysis.lg_light":`licht aan`,"analysis.lg_light_short":`Licht`,"analysis.lg_lux":`lux`,"analysis.tap_block":`Beweeg over de grafiek voor de waarden; tik op een oranje strook (licht aan) voor tijd, bundel en reden. Tik op een legenda-item om het te verbergen.`,"analysis.chart_label":`Tijdlijn: schema, zon, licht aan en lux`,"analysis.in_schedule":`tijdens het schema`,"analysis.partly_schedule":`deels tijdens het schema`,"analysis.outside_schedule":`buiten het schema`,"analysis.no_reason":`Geen reden bekend (alleen voor recente blokken sinds de laatste herstart).`,"analysis.taller":`Groter`,"analysis.smaller":`Kleiner`,"analysis.zoom":`Inzoomen`,"analysis.scroll_hint":`Schuif de grafiek opzij om de rest van de periode te zien.`,"settings.late_home":`Later thuis-knop voor {name}`,"room.late_home":`Aan laten bij Later thuis`,"room.late_home_off":`Uit: de bundels volgen de gewone regels, ook als iemand later thuiskomt.`,"room.late_home_on":`Aan: staat een 'Later thuis'-knop aan, dan gaan de bundels hier niet uit tot die persoon thuis is.`,"room.late_home_active":`Nu actief voor: {names}`,"debug.why.late_home":`'Later thuis' is aan: de bundels blijven aan`,"debug.reason.late_home_arrived":`later thuis: aangekomen`,"late.title":`Later thuis`,"late.active":`aan`,"late.restart":`Herstart Home Assistant om deze knop te maken.`,"late.is_home":`{name} is thuis; Later thuis kan alleen als iemand weg is.`,"late.on_hint":`Aan: ruimten met 'Aan laten bij Later thuis' blijven aan tot deze persoon thuis is. Klik om uit te zetten.`,"late.off_hint":`Klik om aan te zetten: ruimten met 'Aan laten bij Later thuis' blijven aan tot deze persoon thuis is.`,"settings.late_home_short":`Later thuis`,"alarm.home_choose":`Kies wat de lampen in deze ruimte doen:`,"alarm.home_motion":`Op beweging, gedimd`,"alarm.home_no_motion":`Niet op beweging`,"alarm.fixed_home_no_motion":`De lampen gaan uit en reageren niet op beweging, wel op de rest: de wekker, gordijnen die opengaan en handmatig aanzetten.`,"debug.why.armed_home_no_motion":`alarm staat op Armed Home (niet op beweging)`,"debug.wants_armed_home_no_motion":`niet op beweging; wekker en handmatig wel (Armed Home)`,"motion_note.armed_home_no_motion":`het alarm staat op Armed Home en deze ruimte reageert dan niet op beweging`,"media.section":`Mediaspelers`,"media.add":`Mediaspeler toevoegen`,"media.none":`Geen mediaspelers`,"media.none_in_area":`Geen mediaspelers in deze ruimte. Wijs ze eerst toe aan de ruimte in Home Assistant.`,"media.play":`Afspelen`,"media.pause":`Pauze`,"media.state_playing":`Speelt`,"media.state_paused":`Gepauzeerd`,"media.state_idle":`Inactief`,"media.state_on":`Aan`,"media.state_off":`Uit`,"media.state_standby":`Stand-by`,"media.state_buffering":`Laden…`,"media.state_unavailable":`Niet beschikbaar`,"fold.media":`{n} mediaspeler(s)`,"fold.media_playing":`{n} mediaspeler(s) · {playing} speelt`,"info.media":`Voeg de mediaspelers van deze ruimte toe, zoals een TV of speaker. Je ziet wat er speelt en kunt afspelen of pauzeren. Ze veranderen (nog) niets aan de lampen of andere regels.`,"clock.player_room":`Speelt op {player}, de mediaspeler van deze ruimte (sectie Mediaspelers).`,"clock.player_room_many":`Uit de mediaspelers van deze ruimte (sectie Mediaspelers).`,"covers.inverted":`Omgekeerd`,"covers.inverted_chip":`omgekeerd`,"covers.inverted_on":`Aan: RoomControl draait Open en Dicht om voor dit gordijn.`,"covers.inverted_off":`Uit: Open en Dicht gaan zoals Home Assistant ze stuurt.`,"covers.test":`Richting testen`,"covers.test_btn":`Test`,"covers.test_hint":`Stuurt het gordijn 3 seconden open en stopt dan.`,"covers.test_running":`Gordijn gaat 3 seconden open…`,"covers.test_question":`Ging het gordijn open?`,"covers.test_yes":`Ja, klopt`,"covers.test_no":`Nee, ging dicht: omkeren`,"fold.lights":`{n} bundel(s) · {on} aan`,"bundles.none_short":`Nog geen bundels`,"fold.doors":`{n} deursensor(en) · {state}`,"settings.clock_person":`{name} kan gekozen worden bij wekkers`,"settings.clock_person_short":`Wekker`,"clock.covers_title":`Gordijnen`,"clock.covers_on":`Gordijnen openen`,"clock.covers_on_hint":`Aan: de gordijnen gaan open in de stappen van 'Stapsgewijs'.`,"clock.covers_off_hint":`Uit: de wekker laat de gordijnen met rust.`,"clock.covers_same":`Licht en gordijnen samen`,"clock.covers_own":`Apart instellen`,"clock.covers_hint":`Gordijnen zonder positie gaan bij de eerste stap in één keer open. Stop je de wekker, dan blijven de gordijnen staan waar ze zijn.`,"clock.sub_covers_same":`gordijnen mee`,"clock.sub_covers_own":`gordijnen apart`,"clock.snooze_off_hint_covers":`Uit: op de ingestelde tijd gaan de lampen direct aan op 100% en de gordijnen helemaal open.`,"clock.snooze_on_hint_covers":`Aan: licht en gordijnen beginnen zacht en gaan elke interval een stap verder.`,"clock.steps_light":`Licht`,"clock.steps_covers":`Gordijnen`,"clock.covers_on_hint_direct":`Aan: de gordijnen gaan op de wektijd helemaal open.`,"settings.vacuum_person":`{name} is te kiezen bij zuigmomenten en telt mee voor het alarm van de stofzuiger`,"settings.vacuum_person_short":`Stofzuiger`,"vacuum.section":`Stofzuiger`,"vacuum.add":`Stofzuiger kiezen`,"vacuum.none":`Nog geen stofzuiger gekozen.`,"vacuum.none_in_area":`Geen stofzuiger gevonden in Home Assistant.`,"vacuum.add_plan":`Moment toevoegen`,"vacuum.no_plans":`Nog geen zuigmomenten. Kies 'Moment toevoegen'.`,"vacuum.now":`Nu zuigen`,"vacuum.start_failed":`De stofzuiger kon niet starten.`,"vacuum.done_today":`Vandaag gestofzuigd`,"vacuum.not_today":`Vandaag nog niet gestofzuigd`,"vacuum.last":`Laatst gestofzuigd:`,"vacuum.never":`Nog niet gestofzuigd door RoomControl`,"vacuum.fold_plans":`{n} moment(en)`,"vacuum.state_cleaning":`Zuigt`,"vacuum.state_docked":`Op het station`,"vacuum.state_idle":`Inactief`,"vacuum.state_paused":`Gepauzeerd`,"vacuum.state_returning":`Terug naar station`,"vacuum.state_error":`Fout`,"vacuum.state_unavailable":`Niet beschikbaar`,"vacuum.default_name":`Zuigmoment`,"vacuum.sub_always":`altijd`,"vacuum.sub_retry":`anders later, tot {time}`,"vacuum.sub_waiting":`wacht tot iedereen weg is`,"vacuum.retry":`Later proberen`,"vacuum.retry_on":`Aan: mag het op het moment niet, dan start hij zodra het wel mag, tot {time}.`,"vacuum.retry_off":`Uit: klopt het op het moment niet, dan slaat hij dit moment over.`,"vacuum.retry_until":`Tot`,"vacuum.next":`Volgende keer:`,"vacuum.waiting":`Wacht tot iedereen weg is (tot {time}).`,"vacuum.delete_plan":`Moment verwijderen`,"vacuum.alarm_hint":`Start hij terwijl niemand thuis is, dan zet RoomControl het alarm eerst op Armed Home. Is hij klaar en is er nog steeds niemand thuis, dan gaat het alarm op Armed Away. Is er dan iemand thuis, dan blijft het alarm zoals het is.`,"vacuum.alarm_none":`Kies in de instellingen een alarmpaneel om het alarm mee te laten schakelen met de stofzuiger.`,"info.vacuum":`Kies de stofzuiger van deze ruimte en plan zuigmomenten op tijd en dagen, of koppel een schema. Het icoontje is groen als er vandaag gestofzuigd is en wordt grijs als de volgende dag begint.`,"card.vacuumed_today":`Vandaag gestofzuigd`,"card.vacuum_not_today":`Vandaag nog niet gestofzuigd`,"vacuum.schedule_on":`Stofzuigschema`,"vacuum.schedule_on_hint":`Aan: de zuigmomenten hieronder starten de stofzuiger. Ook te schakelen in Home Assistant (schakelaar 'Stofzuigschema' bij het apparaat van de ruimte).`,"vacuum.schedule_off_hint":`Uit: de stofzuiger start niet vanzelf. 'Nu zuigen' werkt nog wel.`,"vacuum.fold_off":`schema uit`,"vacuum.persons_none":`Vink in de instellingen bij personen 'Stofzuiger' aan om ze hier te kunnen kiezen.`,"vacuum.alarm_states":`Of mag bij alarmstand`,"vacuum.alarm_states_chosen":`Of als het alarm in een van deze standen staat.`,"vacuum.alarm_states_any":`Niets gekozen. Kies je bij personen en alarm niets, dan mag het altijd.`,"vacuum.alarm_states_no_panel":`Kies in de instellingen een alarmpaneel; tot die tijd tellen deze standen niet.`,"bundles.on_from":`Tijdens het schema aan`,"bundles.on_from_schedule":`Hele schema`,"bundles.on_from_schedule_hint":`Aan zolang het schema loopt`,"bundles.on_from_dusk":`Vanaf schemer`,"bundles.on_from_dusk_hint":`Aan als het schemert`,"bundles.on_from_dark":`Vanaf donker`,"bundles.on_from_dark_hint":`Aan als het donker is`,"bundles.dusk_ramp":`Geen lux-sensor: tijdens schemer gaat de bundel geleidelijk feller tot {pct}%, mee met de zon. Als het donker is, brandt hij op zijn gewone niveau.`,"bundles.dusk_lux":`Met lux-sensor: tijdens schemer werkt de bundel naar de doel-lux van de ruimte. Als het donker is, brandt hij op zijn gewone niveau.`,"covers.close_at":`Dicht bij`,"covers.close_at_dusk":`Schemer`,"covers.close_at_dark":`Donker`,"covers.open_at":`Open bij`,"covers.open_at_auto":`Met het schema`,"covers.open_at_never":`Niet vanzelf`,"covers.open_at_light":`Licht`,"covers.open_at_time":`Vaste tijd`,"covers.open_at_light_hint":`Open als de zon opkomt (Sun-integratie).`,"covers.open_at_time_hint":`Open op deze tijd, ook als het nog donker is.`,"covers.open_at_auto_hint":`Open als het schema begint en het licht is.`,"covers.open_at_never_hint":`De gordijnen gaan niet vanzelf open.`,"settings.dusk_elevation":`Schemer vanaf zonnehoogte`,"settings.dusk_now":`Nu: zon op {deg}° · {phase}`,"settings.dusk_hint":`Schemer begint als de zon lager staat dan deze hoogte; donker begint als de zon ondergaat. Bundels en gordijnen kunnen op schemer of donker reageren.`,"phase.light":`licht`,"phase.dusk":`schemer`,"phase.dark":`donker`,"card.sun_dusk":`Schemer: de bundels die vanaf schemer aangaan, branden`,"debug.v_light":`licht`,"debug.v_dusk":`schemer`,"debug.v_dark":`donker`,"bundles.t_own_times":`Tijden`,"slots.title":`Wanneer aan`,"slots.none":`Nog geen tijdvakken: de bundel gaat niet vanzelf aan.`,"slots.start":`Begin`,"slots.end":`Eind`,"slots.start_time":`Tijd`,"slots.start_dusk":`Schemer`,"slots.start_dark":`Donker`,"slots.until":`tot`,"slots.end_time":`Tijd`,"slots.end_sunrise":`Zonsopkomst`,"slots.add":`Tijdvak`,"slots.hint":`De bundel gaat aan als een tijdvak begint, met 'Dimmen' aan op die tijd naar Dim (het dim-niveau uit de instellingen) en uit als het tijdvak eindigt (blijft er beweging, dan na de grace period). Eindigt een tijdvak vóór het begin of bij zonsopkomst, dan loopt het door tot de volgende dag.`,"slots.dusk_ramp":`Begint een tijdvak bij schemer, dan begint de bundel op 0% en wordt hij langzaam feller, mee met de zon, tot zijn eigen helderheid als de zon ondergaat.`,"slots.dusk_lux":`Begint een tijdvak bij schemer, dan werkt de bundel tijdens schemer naar de doel-lux, en als het donker is brandt hij op zijn gewone niveau.`,"slots.holiday":`Vakantie`,"slots.vacation_on":`vakantie staat aan`,"slots.vacation_off":`vakantie staat uit`,"slots.holiday_hint":`Tijdvakken 'Normaal' gelden gewoon; staat de modus op Vakantie (algemene instellingen), dan gelden de tijdvakken 'Vakantie' — heeft de bundel die niet, dan blijven de normale gelden.`,"settings.vacation":`Vakantie`,"settings.vacation_title":`Normaal of vakantie`,"settings.vacation_on":`Vakantie: bundels gebruiken hun tijdvakken 'Vakantie' (bijvoorbeeld 's avonds later uit). Ook de schakelaar 'Vakantie' bij het apparaat Generiek in Home Assistant.`,"settings.vacation_off":`Normaal: bundels gebruiken hun tijdvakken 'Normaal'.`,"settings.vacation_missing":`De schakelaar 'Vakantie' is er nog niet; herstart Home Assistant na de update.`,"slots.holiday_normal":`Normaal`,"slots.holiday_vacation":`Vakantie`,"settings.mode_normal":`Normaal`,"settings.mode_vacation":`Vakantie`,"settings.vacation_alarm":`Koppelen aan het alarm`,"settings.vacation_alarm_on":`Aan: staat het alarm op Armed Vacation (Vakantie), dan gaat de modus op Vakantie; gaat het alarm uit die stand, dan weer op Normaal. Je kunt de modus ook zelf wisselen.`,"settings.vacation_alarm_off":`Uit: je wisselt de modus zelf (hier of met de schakelaar 'Vakantie' in Home Assistant).`,"settings.vacation_alarm_no_panel":`Kies eerst een alarmpaneel hierboven.`,"bundles.convert_title":`Schema van de ruimte vervangen door tijden`,"bundles.convert_hint":`Deze bundels volgen nog het schema van de ruimte: {names}. Zet ze om: ze krijgen dezelfde dagen en tijden als tijdvakken, en het schema wordt losgekoppeld.`,"bundles.convert_btn":`Omzetten`,"bundles.convert_not_found":`Het schema is niet gevonden in Home Assistant (alleen schema's die in de interface zijn gemaakt kunnen worden overgenomen).`,"bundles.convert_failed":`Omzetten lukte niet.`,"slots.name":`Naam van het tijdvak`,"slots.name_placeholder":`Tijdvak`,"settings.dim":`Dim`,"settings.dim_level":`Dim-niveau`,"settings.dim_level_hint":`Hoe fel lampen branden als Dim aan staat: de Dim-knop, Dim bij Armed Home en 'Dim vanaf' in een tijdvak (als dat geen eigen niveau heeft). Standaard 1%.`,"slots.dim_at":`om`,"slots.dim":`Dimmen`,"analysis.lg_target":`doel-lux`,"analysis.tip_light_on":`licht aan`,"analysis.tip_light_off":`licht uit`,"analysis.tip_sched_off":`geen schema`,"analysis.tip_sun_down":`zon onder`,"analysis.tip_sun_up":`zon op`,"bundles.convert_unused":`Deze ruimte heeft nog een schema, maar geen bundel gebruikt het meer. Koppel het los (de gordijnen gaan dan alleen nog dicht bij schemer of donker).`,"bundles.unlink_btn":`Loskoppelen`,"vacuum.home_persons":`Mag als thuis`,"vacuum.home_chosen":`Mag als minstens één van deze personen thuis is.`,"vacuum.home_anyone":`Niemand gekozen.`,"vacuum.sub_home":`als {names} thuis is`,"vacuum.sub_alarm":`bij {states}`,"vacuum.or":`of`,"clock.summary_no_stop":`Hij stopt niet vanzelf.`,"clock.volume_first":`Volume eerste stap`,"clock.volume_last":`Volume laatste stap`,"clock.stop_step":`stopstap`,"clock.stop_music":`Muziek uit`,"clock.stop_light":`Licht uit`,"clock.stop_what_both":`muziek en licht uit`,"clock.stop_what_music":`muziek uit`,"clock.stop_what_light":`licht uit`,"clock.stop_what_none":`stopt niet`,"clock.stop_hint":`De stopstap volgt één interval na de laatste stap, als niemand de wekker heeft gestopt.`,"clock.stop_none_warn":`Niets aangevinkt bij de stopstap: de wekker stopt niet vanzelf.`,"clock.pill_steps":`{n} stappen`,"clock.pill_every":`elke {min} min`,"clock.pill_direct":`Direct 100%`,"clock.pill_off":`Uit`,"clock.pill_open":`Openen`,"clock.pill_covers_same":`Samen met licht`,"clock.pill_covers_own":`Apart`,"clock.pill_covers_direct":`Direct open`,"clock.pill_pick":`Kies speler en muziek`,"locks.section":`Sloten`,"locks.add":`Slot toevoegen`,"locks.none":`Geen sloten`,"locks.none_in_area":`Geen sloten in deze ruimte. Wijs ze eerst toe aan de ruimte in Home Assistant.`,"locks.fold":`{n} slot(en) · {locked} op slot`,"locks.hint":`RoomControl doet een slot alleen vanzelf op slot, nooit open. In Home Assistant staat elk slot ook op het apparaat van de ruimte.`,"info.locks":`Voeg de sloten van deze ruimte toe. Per slot stel je de tijden in waarop het op slot gaat, of het op slot gaat als niemand thuis is, en of het paneel vraagt voordat het slot opengaat.`,"locks.state_locked":`Op slot`,"locks.state_open":`Open`,"locks.state_jammed":`Klemt`,"locks.state_moving":`Bezig…`,"locks.state_unknown":`Onbekend`,"locks.open":`Openen`,"locks.lock":`Op slot`,"locks.since":`sinds`,"locks.confirm_q":`Weet je zeker dat je {name} wilt openen?`,"locks.cancel":`Annuleren`,"locks.confirm_yes":`Ja, openen`,"locks.options":`Opties`,"locks.away":`Op slot als niemand thuis is`,"locks.away_hint":`Als iedereen (personen in de algemene instellingen) {min} min weg is, gaat het slot op slot. Ook als het opengaat terwijl niemand thuis is.`,"locks.away_after":`Wachttijd`,"locks.confirm":`Bevestigen voor openen`,"locks.confirm_hint":`Het paneel vraagt eerst of het slot echt open moet. In Home Assistant gaat het slot direct open.`,"locks.never_opens":`Vaste tijden en 'niemand thuis' doen dit slot alleen op slot, nooit open.`,"locks.remove":`Slot verwijderen`,"locks.pill_no_slots":`Geen tijden`,"locks.pill_slots_off":`Alle tijden uit`,"locks.pill_away":`Niemand thuis · {min} min`,"locks.pill_confirm":`Bevestigen bij openen`,"locks.times_title":`Wanneer op slot`,"locks.times_none":`Nog geen tijden: het slot gaat niet op een vaste tijd op slot.`,"locks.times_hint":`Op deze tijd gaat het slot op slot, op de gekozen dagen. Is het al op slot, dan gebeurt er niets. Met de schakelaar zet je een tijd uit zonder hem te verwijderen.`,"locks.time_at":`Op slot om`,"locks.time_add":`Tijd`,"locks.time_name_placeholder":`Tijd`,"alarm.away_choose":`Er is niemand thuis. Kies wat de lampen in deze ruimte doen:`,"alarm.away_off":`Uitzetten`,"alarm.away_follow":`Niet uitzetten, tijdvak volgen`,"locks.time_on":`Deze tijd aan`,"locks.time_off":`Uit`,"smart.section":`Slim`,"info.smart":`Slimme opties leren van hoe de ruimte gebruikt wordt. Alles blijft lokaal in Home Assistant. Het gedrag van de ruimte (wanneer lampen aan zijn, beweging per uur) wordt altijd bijgehouden, zodat een optie meteen gegevens heeft als je hem aanzet.`,"smart.fold_none":`Geen slimme opties aan`,"smart.fold":`{n} slimme optie(s) aan`,"smart.forget":`Opnieuw leren`,"smart.needs_motion":`Werkt alleen met een bewegingssensor in deze ruimte.`,"smart.needs_media":`Voeg eerst een mediaspeler toe aan deze ruimte.`,"smart.grace":`Grace period leert mee`,"smart.grace_hint":`Gaan de lampen uit en is er binnen een minuut weer beweging, dan wordt de grace period 1 minuut langer. Klopte het uitzetten, dan wordt hij langzaam weer korter (tot maximaal 15 minuten extra).`,"smart.grace_status":`Nu {min} min langer dan ingesteld`,"smart.grace_status_none":`Nog niets geleerd: de ingestelde grace period geldt`,"smart.media":`Media houdt de ruimte bezet`,"smart.media_hint":`Zolang een mediaspeler van deze ruimte speelt, gepauzeerd is of aan staat, gaan de lampen niet uit door gebrek aan beweging.`,"smart.media_status":`Er speelt nu media: de lampen blijven aan`,"smart.last_motion":`Iemand is hier nog`,"smart.last_motion_hint":`Was de laatste beweging in huis in deze ruimte, dan is hier waarschijnlijk nog iemand. De lampen blijven aan tot er ergens anders beweging is, maximaal 45 minuten. Daarna geldt de grace period.`,"smart.last_motion_status":`Laatste beweging in huis was hier: nog {min} min aan`,"smart.brightness":`Helderheid leren`,"smart.brightness_hint":`Zet je een lamp met de hand feller of zachter, dan onthoudt de ruimte dat per uur van de dag. Na drie keer wordt dat de standaardhelderheid voor dat uur.`,"smart.brightness_status":`{n} lamp-uren geleerd`,"smart.replay":`Bewoond lijken`,"smart.replay_hint":`Is er niemand thuis (of staat het alarm op Armed Away) en is het donker, dan gaan de lampen aan en uit zoals op dezelfde weekdag de vorige keer, elke dag een paar minuten verschoven.`,"smart.replay_status":`{n} dag(en) gedrag onthouden`,"smart.replay_status_active":`Nu actief: de lampen volgen het gedrag van vorige week`,"smart.anomaly":`Ongewone activiteit melden`,"smart.anomaly_hint":`Een melding in Home Assistant bij beweging op een tijdstip waarop hier nooit iemand is, en als de lampen 3 uur branden zonder beweging. Er gaat ook een event roomcontrol_anomaly uit, zodat je zelf een pushbericht kunt maken.`,"smart.anomaly_status_learning":`Aan het leren ({weeks} weken): meldingen over beweging na 2 weken`,"smart.anomaly_status_ready":`{weeks} weken geleerd`,"debug.reason.grace_learned":`grace period aangepast`,"debug.reason.brightness_learned":`helderheid geleerd`,"debug.reason.replay":`bewoond lijken`,"debug.reason.replay_end":`bewoond lijken gestopt`,"debug.reason.anomaly_motion":`ongewone beweging gemeld`,"debug.reason.anomaly_lights_on":`lampen lang aan gemeld`,"smoke.section":`Rookmelders`,"smoke.hint":`Zet aan welke rookmelders RoomControl volgt. Bij rook in één ruimte doet RoomControl in het hele huis wat hieronder aan staat, en daarna niets automatisch meer tot je op 'Alles veilig' drukt.`,"smoke.none":`Geen rookmelders gevonden (binary_sensor met device class smoke).`,"smoke.detected":`Rook!`,"smoke.offline":`Niet bereikbaar`,"smoke.battery_low":`Batterij bijna leeg`,"smoke.battery":`batterij`,"smoke.clear_state":`Geen rook`,"smoke.actions_title":`Bij rook, ergens in huis`,"smoke.action_lights":`Alle lampen vol aan`,"smoke.action_lights_hint":`In alle ruimten 100%, wit licht waar de lamp dat kan. Gaat voor schema, alarm, Dim en handmatig.`,"smoke.action_fans":`Ventilatoren uit`,"smoke.action_fans_hint":`Zodat rook niet door het huis wordt getrokken. Ze blijven uit tot 'Alles veilig'.`,"smoke.action_covers":`Gordijnen open`,"smoke.action_covers_hint":`Zicht naar buiten, en voor hulpdiensten naar binnen.`,"smoke.action_locks":`Sloten openen`,"smoke.action_locks_hint":`Alleen als er iemand thuis is, zodat de vluchtweg vrij is. Het enige moment dat RoomControl een slot opent.`,"smoke.action_media":`Media stoppen en waarschuwen`,"smoke.action_media_hint":`Muziek en tv in de ruimten stoppen. De speakers van Omroepen zeggen waar de rook is.`,"smoke.action_vacuum":`Stofzuiger terug naar het dock`,"smoke.action_vacuum_hint":`Zodat hij de vluchtweg niet blokkeert. Schoonmaakmomenten wachten tot 'Alles veilig'.`,"smoke.action_maintenance":`Melding bij lege batterij of storing`,"smoke.action_maintenance_hint":`Een melding in Home Assistant als de batterij onder 20% is, of als een melder 24 uur niet bereikbaar is.`,"smoke.banner_title":`Rook gedetecteerd · {where} · {time}`,"smoke.banner_hint":`RoomControl doet niets automatisch tot je bevestigt dat alles veilig is.`,"smoke.banner_still":`Een rookmelder meldt nog rook. Na 'Alles veilig' gaat het alarm dan meteen weer af.`,"smoke.clear":`Alles veilig`,"doorbell.section":`Deurbel`,"info.doorbell":`Kies de deurbel van deze ruimte. Bij een UniFi Protect-deurbel worden de camera en het schermpje van hetzelfde apparaat er automatisch bij gezocht. RoomControl doet niets met de lampen als er wordt aangebeld.`,"doorbell.none":`Geen deurbel gekozen`,"doorbell.off":`Geen`,"doorbell.entity":`Deurbel`,"doorbell.pick_hint":`Kies de deurbel (event of binary_sensor).`,"doorbell.last":`laatst gebeld`,"doorbell.never":`Nog niet aangebeld sinds de laatste herstart`,"doorbell.camera":`Camera`,"doorbell.camera_hint":`Een stilstaand beeld gaat mee in de melding.`,"doorbell.no_camera":`Geen`,"doorbell.on_ring":`Bij aanbellen`,"doorbell.pause":`Media pauzeren`,"doorbell.pause_hint":`Tv en muziek pauzeren in ruimten waar iemand is (beweging in de laatste 10 minuten, of ruimten zonder bewegingssensor).`,"doorbell.announce":`Aankondigen op speakers`,"doorbell.announce_hint":`De speakers van die ruimten zeggen dat er iemand bij de deur staat (zie Omroepen in de algemene instellingen).`,"doorbell.announce_no_tts":`Kies eerst een spraakdienst bij Omroepen in de algemene instellingen.`,"doorbell.notify":`Melding`,"doorbell.notify_hint":`Een melding in Home Assistant (met camerabeeld) en een event roomcontrol_doorbell, waarmee je zelf een pushbericht kunt maken.`,"doorbell.quiet":`Stil 's nachts`,"doorbell.quiet_hint":`In deze uren alleen de melding: niet pauzeren of aankondigen.`,"doorbell.quiet_from":`Stil vanaf`,"doorbell.quiet_to":`Stil tot`,"doorbell.screen":`Schermpje van de deurbel`,"doorbell.screen_none":`Deze deurbel heeft geen schermpje dat RoomControl kan instellen.`,"doorbell.away_message":`Bericht als niemand thuis is`,"doorbell.away_message_hint":`Zolang niemand thuis is toont de deurbel dit bericht. Komt er iemand thuis, dan komt het vorige bericht terug.`,"doorbell.pick_message":`Kies een bericht`,"doorbell.message_placeholder":`Pakket bij de buren`,"bundles.auto_max":`Helderheid automatisch`,"bundles.auto_max_hint":`Bij beweging en tijden gaan de lampen aan op {pct}%, en de luxsensor maakt ze nooit feller. Met de hand kun je ze feller zetten; dat blijft zo tot de lamp uitgaat.`,"bundles.auto_max_none":`Nog geen niveau gekozen: de lampen gaan aan op hun eigen laatste helderheid. Schuif om een niveau te kiezen.`,"bundles.sub_max":`{pct}%`,"bundles.restore":`Terug naar automatische helderheid`,"debug.reason.brightness_by_hand":`helderheid met de hand aangepast`,"debug.reason.restore":`terug naar automatisch`,"smoke.action_switches":`Apparaten uit`,"smoke.action_switches_hint":`Deze schakelaars gaan meteen uit, bijvoorbeeld de espressomachine, een kachel of de tv. Bij 'Alles veilig' gaan de schakelaars die aan stonden weer aan.`,"smoke.switches_pick":`Kies een schakelaar…`,"smoke.switches_add":`Nog een schakelaar…`,"announce.section":`Omroepen`,"announce.hint":`Eén bericht tegelijk op de speakers van het huis. Rookmelders, deurbel en je eigen automatiseringen gebruiken dit. Een ruimte met gekoppelde personen (Aanwezigheid) doet alleen mee als een van hen thuis is.`,"announce.tts":`Spraakdienst`,"announce.tts_hint":`Spreekt de berichten uit op de mediaspelers.`,"announce.tts_none":`Geen spraakdienst (tts.*) in Home Assistant: omroepen werkt niet.`,"announce.tts_off":`Geen`,"announce.test":`Omroepen`,"announce.test_placeholder":`Eten is klaar`,"announce.sent":`Verstuurd naar {n} speaker(s).`,"announce.sent_none":`Geen speaker doet nu mee: er is niets verstuurd.`,"announce.failed":`Versturen mislukt.`,"announce.now_title":`Wie krijgt een bericht nu`,"announce.none":`Nog geen mediaspelers in de ruimten. Voeg ze toe bij Mediaspelers in een ruimte.`,"announce.status_on":`Doet mee`,"announce.status_away":`Overgeslagen`,"announce.status_off":`Doet niet mee`,"announce.why_off":`Uitgezet bij de mediaspelers van de ruimte`,"announce.why_no_persons":`Geen personen gekoppeld: doet altijd mee`,"announce.why_home":`Thuis: {names}`,"announce.why_away":`Niet thuis: {names}`,"announce.service_hint":`In automatiseringen: actie roomcontrol.announce met een bericht en eventueel ruimten, of de melding-entiteiten Omroepen van RoomControl.`,"announce.room_title":`Omroepen`,"announce.room_no_persons":`Geen personen gekoppeld bij Aanwezigheid: deze speakers doen altijd mee.`,"announce.room_persons_home":`Doen mee zolang een van deze personen thuis is: {names}. Nu is er iemand thuis.`,"announce.room_persons_away":`Doen mee zolang een van deze personen thuis is: {names}. Nu is niemand van hen thuis.`,"card.clock_next":`Wekker: {when}`,"card.clock_ringing":`Wekker gaat nu af`,"card.lock_locked":`Op slot`,"card.lock_open":`Open: {names}`,"card.lock_problem":`Slot heeft een probleem: {names}`,"card.door_closed":`Deur dicht`,"card.door_open":`Deur open: {names}`,"announce.save":`Bericht bewaren`,"announce.use":`Dit bericht gebruiken`,"texts.section":`Teksten`,"texts.hint":`De teksten die RoomControl uitspreekt of als melding stuurt. Laat een veld leeg voor de standaardtekst (grijs). Bij gesproken teksten kies je het volume; 'Huidig' laat de speakers op hun eigen volume. Na het bericht gaat het volume terug.`,"texts.reset":`Standaardtekst gebruiken`,"texts.placeholders":`invullen:`,"texts.anomaly_motion":`Ongewone beweging`,"texts.anomaly_lights_on":`Lampen lang aan`,"texts.grp_smoke":`Teksten bij rook`,"texts.grp_doorbell":`Bij aanbellen`,"texts.grp_alerts":`Meldingen`,"texts.grp_announce":`Omroepen (eigen berichten)`,"texts.spoken":`Gesproken`,"texts.notify":`Melding`,"texts.smoke_battery_short":`Lege batterij`,"texts.smoke_offline_short":`Niet bereikbaar`,"texts.volume":`Volume`,"texts.volume_own":`Huidig`,"texts.volume_clear":`Volume van de speaker zelf houden`,"texts.announce_note":`Testbericht, bewaarde berichten en roomcontrol.announce`,"debug.kind.lock":`slot`,"debug.kind.door":`deur`,"debug.reason.door_open":`deur open`,"debug.reason.door_closed":`deur dicht`,"debug.reason.lock_state_locked":`op slot`,"debug.reason.lock_state_unlocked":`van het slot`,"debug.reason.lock_state_open":`open`,"debug.reason.lock_state_jammed":`klemt`,"debug.reason.lock_state_unavailable":`niet bereikbaar`,"debug.reason.lock_state_unknown":`onbekend`,"debug.reason.lock_time":`op slot gedaan: sluittijd`,"debug.reason.lock_away":`op slot gedaan: niemand thuis`,"debug.reason.lock_missed":`op slot gedaan: gemiste sluittijd (herstart)`,"debug.reason.lock_missed_found":`sluittijd gemist tijdens herstart, wordt ingehaald`,"debug.reason.lock_missed_gave_up":`gemiste sluittijd niet ingehaald: slot bleef onbereikbaar`,"debug.reason.lock_unavailable":`sluittijd, maar het slot is niet bereikbaar`,"debug.reason.lock_already_locked":`sluittijd: al op slot`,"debug.reason.lock_failed":`op slot doen mislukt`,"debug.lock_at":`tijd`,"debug.now_locks":`Sloten`,"debug.now_doors":`Deuren`,"debug.since":`sinds`,"debug.lock_next":`volgende sluittijd`,"debug.lock_no_times":`geen sluittijden aan`,"debug.lock_away":`op slot na {min} min niemand thuis`,"debug.lock_nobody_since":`niemand thuis sinds`,"debug.lock_catch_up":`wacht om gemiste tijd in te halen:`,"debug.lock_state.locked":`Op slot`,"debug.lock_state.unlocked":`Open`,"debug.lock_state.open":`Open`,"debug.lock_state.jammed":`Klemt`,"debug.lock_state.locking":`Bezig`,"debug.lock_state.unlocking":`Bezig`,"debug.lock_state.unavailable":`Niet bereikbaar`,"debug.lock_state.unknown":`Onbekend`,"debug.lock_state.missing":`Ontbreekt`,"debug.door_open":`Open`,"debug.door_closed":`Dicht`,"fold.less":`Minder tonen`,"fold.link_motion":`deelt beweging`,"fold.last":`laatst`,"fold.since":`sinds`,"fold.battery":`batterij`,"fold.battery_low":`bijna leeg`,"fold.unavailable":`Niet bereikbaar`,"door.none_hint":`Geen deursensoren. Een deur die opengaat kan lampen aanzetten, net als beweging.`,"smart.show_more":`Toon meer`,"smart.show_less":`Toon minder`}};function V(e,t=`en`){return Ne[t.split(`-`)[0]]?.[e]??Ne.en?.[e]??e}var Pe=`roomcontrol`;async function Fe(e){return e.callWS({type:`${Pe}/get_config`})}async function Ie(e,t){await e.callWS({type:`${Pe}/set_config`,config:t})}async function Le(e,t){await e.callWS({type:`${Pe}/set_config`,config:{settings:t}})}async function Re(e,t,n){await e.callWS({type:`${Pe}/set_dim`,dim:t,...n?{area_id:n}:{}})}async function ze(e,t,n){await e.callWS({type:`${Pe}/set_manual`,area_id:t,...n===void 0?{}:{minutes:n}})}async function H(e,t,n,r){let{entity_id:i,...a}=r;await e.callWS({type:`${Pe}/call_service`,domain:t,service:n,entity_id:i,data:a})}async function Be(e,t,n){for(let r of t)await H(e,`light`,`turn_on`,{entity_id:r,...n===void 0?{}:{brightness:n}})}async function Ve(e,t){for(let n of t)await H(e,`light`,`turn_off`,{entity_id:n})}async function He(e,t,n){for(let r of t)e.states[r]?.state===`on`&&await H(e,`light`,`turn_on`,{entity_id:r,brightness:n})}async function Ue(e,t,n,r){let i=Object.values(e.states).find(e=>e.entity_id.startsWith(`light.`)&&e.attributes.roomcontrol_area===t);i?await H(e,`light`,r?`turn_on`:`turn_off`,{entity_id:i.entity_id}):r?await Be(e,n):await Ve(e,n)}function We(e){let t=e.fixed_levels??{};return e.lights.map(e=>e.entity_id).filter(e=>!(e in t))}async function Ge(e,t,n,r={}){if(t.length===0)return;if(!n){await H(e,`light`,`turn_off`,{entity_id:t});return}let i=t.filter(e=>!(e in r));i.length&&await H(e,`light`,`turn_on`,{entity_id:i});for(let n of t.filter(e=>e in r))await H(e,`light`,`turn_on`,{entity_id:n,brightness_pct:r[n]})}async function Ke(e,t,n){t.length&&await H(e,`cover`,n,{entity_id:t})}function qe(e,t,n){return{area_id:t,name:n,lights:[],motion_sensor:``,motion_sensors:[],motion_off_delay:300,manual_duration:60,linked_rooms:[],turn_on_at_dusk:!1,sun_entity:`sun.sun`,lux_sensor:``,target_lux:0,turn_off_on_armed_home:!1,alarm_entity:``,schedules:[],schedule_selector:``}}function Je(e,t){let n=new Map(t.map(e=>[e.area_id,e])),r=Object.values(e.areas??{}).sort((t,n)=>t.name.localeCompare(n.name,e.language)),i=r.map(t=>n.get(t.area_id)??qe(e,t.area_id,t.name)),a=new Set(r.map(e=>e.area_id));return[...i,...t.filter(e=>!a.has(e.area_id))]}function Ye(e,t){let n=e.entities?.[t];return n?n.area_id?n.area_id:n.device_id?e.devices?.[n.device_id]?.area_id??null:null:null}function U(e,t,n,r){return Object.keys(e.states).filter(e=>e.startsWith(`${n}.`)).filter(t=>e.entities?.[t]?.platform!==`roomcontrol`).filter(n=>Ye(e,n)===t).filter(t=>!r||r.includes(String(e.states[t].attributes.device_class??``))).sort()}var Xe=[`linked_rooms`,`fan_shared_rooms`];function Ze(e,t,n=`linked_rooms`){let r=e.find(e=>e.area_id===t)?.[n]??[],i=e.filter(e=>(e[n]??[]).includes(t)).map(e=>e.area_id);return[...new Set([...r,...i])].filter(e=>e!==t)}function Qe(e,t,n=`linked_rooms`){let r=new Set([t]),i=[t];for(;i.length;)for(let t of Ze(e,i.pop(),n))r.has(t)||(r.add(t),i.push(t));return[...r].sort()}function $e(e,t,n){let r=new Set(t[n]??[]);return Qe([...e.filter(e=>e.area_id!==t.area_id).map(e=>({...e,[n]:(e[n]??[]).filter(n=>n!==t.area_id||r.has(e.area_id))})),t],t.area_id,n)}function et(e,t,n){let r=Object.fromEntries(Xe.map(e=>[e,new Set(n[e]??[])])),i=t.filter(e=>e.area_id!==n.area_id).map(e=>{let t=e;for(let i of Xe){let a=new Set(e[i]??[]),o=a.has(n.area_id);r[i].has(e.area_id)?a.add(n.area_id):a.delete(n.area_id),o!==a.has(n.area_id)&&(t={...t,[i]:[...a]})}return t}),a=[];for(let t of Xe)for(let o of r[t]){if(i.some(e=>e.area_id===o))continue;let r=a.find(e=>e.area_id===o);r?r[t]=[...r[t]??[],n.area_id]:a.push({...qe(e,o,e.areas?.[o]?.name??o),[t]:[n.area_id]})}let o=t.findIndex(e=>e.area_id===n.area_id);return o===-1?i.push(n):i.splice(o,0,n),[...i,...a]}function tt(e,t=`linked_rooms`){let n=new Set,r=[];for(let i of e){if(n.has(i.area_id))continue;let a=Qe(e,i.area_id,t);a.forEach(e=>n.add(e)),a.length>1&&r.push(a)}return r}function nt(e,t,n=`linked_rooms`){let r=new Map(t.map(r=>[r,Ze(e,r,n).filter(e=>t.includes(e))])),i=(e,t)=>(r.get(e)??[]).includes(t),a=[...t].sort((e,t)=>(r.get(e)?.length??0)-(r.get(t)?.length??0)||e.localeCompare(t))[0],o=[],s=[a],c=new Set([a]);for(;s.length;){let e=s.shift();o.push(e);for(let t of r.get(e)??[])c.has(t)||(c.add(t),s.push(t))}let l=(e,t)=>{let n=new Map,i=[e],a=new Set([e]);for(;i.length;){let e=i.shift();if(e===t)break;for(let t of r.get(e)??[])a.has(t)||(a.add(t),n.set(t,e),i.push(t))}let o=[];for(let r=n.get(t);r&&r!==e;r=n.get(r))o.unshift(r);return o},u=[];for(let e=0;e<o.length;e++)for(let t=e+1;t<o.length;t++)i(o[e],o[t])||u.push({a:o[e],b:o[t],through:l(o[e],o[t])});return{order:o,direct:i,via:u}}function rt(e,t){let n=(t.schedules??[]).filter(Boolean);if(n.length===0)return null;if(!t.schedule_selector)return n[0];let r=e.states[t.schedule_selector]?.state,i=r===void 0?0:Math.trunc(Number(r));return Number.isFinite(i)&&i>=1&&i<=n.length?n[i-1]:null}function it(e,t){let n=rt(e,t);if(!n)return!0;let r=e.states[n]?.state;return r!==`on`&&r!==`off`||r===`on`}function W(e){return(e.motion_sensors??(e.motion_sensor?[e.motion_sensor]:[])).filter(Boolean)}function at(e){return(e.lux_sensors??(e.lux_sensor?[e.lux_sensor]:[])).filter(Boolean)}var ot=[`average`,`min`,`max`,`median`,`sum`];function st(e,t){if(e.length===0)return null;switch(t??`average`){case`min`:return Math.min(...e);case`max`:return Math.max(...e);case`sum`:return e.reduce((e,t)=>e+t,0);case`median`:{let t=[...e].sort((e,t)=>e-t),n=Math.floor(t.length/2);return t.length%2?t[n]:(t[n-1]+t[n])/2}default:return e.reduce((e,t)=>e+t,0)/e.length}}function ct(e,t){return st(at(t).map(t=>e.states[t]?.state).filter(e=>e!==void 0&&e!==``&&Number.isFinite(Number(e))).map(Number),t.lux_mode)}function lt(e,t){return(e.persons??[]).filter(e=>t.includes(e))}function ut(e,t,n=[]){let r=t.lights.map(t=>e.states[t.entity_id]).filter(Boolean),i=r.filter(e=>e.state===`on`),a=i.length>0,o=r.length>0&&i.length===r.length,s=i.map(e=>Number(e.attributes.brightness)).filter(e=>!isNaN(e)),c=s.length>0?Math.round(s.reduce((e,t)=>e+t,0)/s.length):null,l=W(t).some(t=>{let n=e.states[t]?.state;return n===`on`||n===`detected`}),u=t.sun_entity||`sun.sun`,d=e.states[u]?.state===`below_horizon`,f=ct(e,t),p=at(t).length>0&&t.target_lux>0&&t.target_lux_enabled!==!1,m=lt(t,n).map(t=>({entity_id:t,home:e.states[t]?.state===`home`})),h=m.length===0||m.some(e=>e.home),g=t.turn_on_at_dusk&&e.states[t.sun_entity||`sun.sun`]?.state===`below_horizon`;return{area_id:t.area_id,any_on:a,all_on:o,avg_brightness:c,motion_detected:l,is_dusk:d,current_lux:f,lux_control_active:p,active_schedule:rt(e,t),schedule_allows:it(e,t),persons:m,presence_allows:h,dusk_override:g,allowed:h&&(it(e,t)||g),status:a?`active`:`standby`}}function dt(e){return e===null?`—`:`${Math.round(e/255*100)}%`}function ft(e,t=`sun.sun`,n=2200,r=5e3){let i=e.states[t]?.attributes.elevation;if(typeof i!=`number`)return null;let a=Math.min(n,r),o=Math.max(n,r),s=Math.min(1,Math.max(0,(i+6)/46));return Math.round((a+s*(o-a))/50)*50}function pt(e){let t=Math.min(4e4,Math.max(1e3,e))/100,n=e=>Math.min(255,Math.max(0,e)),r=t<=66?255:n(329.698727446*(t-60)**-.1332047592),i=n(t<=66?99.4708025861*Math.log(t)-161.1195681661:288.1221695283*(t-60)**-.0755148492),a=t>=66?255:t<=19?0:n(138.5177312231*Math.log(t-10)-305.0447927307);return[Math.round(r),Math.round(i),Math.round(a)]}function G(e,t){return Object.values(e.states).find(e=>e.entity_id.startsWith(`light.`)&&e.attributes.roomcontrol_area===t)}function mt(e,t){return G(e,t)?.attributes.dimmed===!0}function ht(e,t,n=Date.now()){let r=G(e,t)?.attributes.grace_until;if(typeof r!=`string`)return null;let i=Math.ceil((Date.parse(r)-n)/1e3);return i>0?i:null}function K(e){let t=Math.max(0,Math.round(e));return`${Math.floor(t/60)}:${String(t%60).padStart(2,`0`)}`}function gt(e,t,n=Date.now()){let r=G(e,t)?.attributes.manual_until;if(typeof r!=`string`)return null;let i=Math.ceil((Date.parse(r)-n)/1e3);return i>0?i:null}function _t(e){let t=Math.max(0,Math.round(e)),n=Math.floor(t/3600),r=Math.floor(t%3600/60),i=String(t%60).padStart(2,`0`);return n>0?`${n}:${String(r).padStart(2,`0`)}:${i}`:`${r}:${i}`}function vt(e,t){let n=Math.floor(e/60),r=e%60;return n===0?`${r} min`:r===0?`${n} ${t}`:`${n} ${t} ${r} min`}function yt(e){for(let t of Object.values(e.states)){if(!t.entity_id.startsWith(`light.`)||!t.attributes.roomcontrol_area)continue;let e=t.attributes.smoke;if(e)return e}return null}function bt(e,t){let n=e.entities?.[t]?.device_id;if(!n)return null;for(let r of Object.values(e.entities))if(r.device_id===n&&r.entity_id!==t&&e.states[r.entity_id]?.attributes.device_class===`battery`&&/^(sensor|binary_sensor)\./.test(r.entity_id))return r.entity_id;return null}function xt(e){let t=``;do t=`g${Date.now().toString(36)}${Math.random().toString(36).slice(2,6)}`;while(e.some(e=>e.id===t));return t}function St(e,t){return e.lights.map(e=>e.entity_id).filter(e=>t.includes(e))}function Ct(e,t,n){let r=e.groups??[],i={id:xt(r),name:t.trim(),lights:St(e,n)};return{...e,groups:[...r,i]}}function wt(e,t,n){return{...e,groups:(e.groups??[]).map(e=>e.id===t?{...e,name:n}:e)}}function Tt(e,t,n){return{...e,groups:(e.groups??[]).map(r=>r.id===t?{...r,lights:St(e,n)}:r)}}function Et(e,t){return{...e,groups:(e.groups??[]).filter(e=>e.id!==t)}}function Dt(e,t){return e.groups?.length?{...e,groups:e.groups.map(e=>({...e,lights:e.lights.filter(e=>e!==t)}))}:e}function Ot(e,t,n){return e.name.trim()||`${n} ${t+1}`}function kt(e,t){let n=t.lights.map(t=>e.states[t]).filter(e=>e?.state===`on`),r=n.map(e=>Number(e.attributes.brightness)).filter(e=>!isNaN(e));return{any_on:n.length>0,avg_brightness:r.length?Math.round(r.reduce((e,t)=>e+t,0)/r.length):null}}function At(e,t,n){let r=e.fixed_levels??{},i=t.map(e=>r[e]).filter(e=>typeof e==`number`),a=i.length===t.length&&t.length>0&&i.every(e=>e===i[0]),o=e.daylight_lights;return{brightness_mode:a?`fixed`:`default`,brightness:a?i[0]:e.default_brightness??0,follow_daylight:!!e.follow_daylight&&(o===void 0||t.some(e=>o.includes(e))),daylight_prefer_rgb:!!e.daylight_prefer_rgb,daylight_min_kelvin:e.daylight_min_kelvin??2200,daylight_max_kelvin:e.daylight_max_kelvin??5e3,on_motion:!0,on_door:!!e.door_turn_on&&!!n&&(e.door_groups??[]).includes(n),on_dusk:!!e.turn_on_at_dusk,follow_schedule:!0,dim:!0,lux_control:!!e.lux_control,away_follow_schedule:!1,on_from:`schedule`,own_times:!1,slots:[]}}function jt(e){return e.flatMap(e=>e.lights)}function Mt(e,t){return{...e,groups:t,lights:jt(t).map(e=>({entity_id:e}))}}function Nt(e,t=`Lampen`){let n=e.lights.map(e=>e.entity_id),r=new Set,i=[];for(let t of e.groups??[]){let a=t.lights.filter(e=>n.includes(e)&&!r.has(e));a.forEach(e=>r.add(e)),a.length&&i.push({...At(e,a,t.id),...t,lights:a})}let a=n.filter(e=>!r.has(e));return a.length&&i.push({...At(e,a),id:xt(i),name:t,lights:a}),Mt(e,i)}function Pt(e,t,n){let r=e.groups??[],i=new Set(jt(r)),a=t.filter(e=>!i.has(e));if(!a.length)return e;let o={...At(e,[]),follow_schedule:!1,id:xt(r),name:n,lights:a};return Mt(e,[...r,o])}function Ft(e,t,n){let r=e.groups??[],i=new Set(jt(r)),a=n.filter(e=>!i.has(e));return Mt(e,r.map(e=>e.id===t?{...e,lights:[...e.lights,...a]}:e))}function It(e,t){let n=(e.groups??[]).map(e=>({...e,lights:e.lights.filter(e=>e!==t)})).filter(e=>e.lights.length>0),r={...e.fixed_levels??{}};return delete r[t],{...Mt(e,n),fixed_levels:r}}function Lt(e,t,n){return Mt(e,(e.groups??[]).map(e=>e.id===t?{...e,...n}:e))}function Rt(e,t){return{...Mt(e,(e.groups??[]).filter(e=>e.id!==t)),door_groups:(e.door_groups??[]).filter(e=>e!==t)}}function zt(e,t,n){let r=[...e.groups??[]],i=r.findIndex(e=>e.id===t),a=i+n;return i<0||a<0||a>=r.length?e:([r[i],r[a]]=[r[a],r[i]],Mt(e,r))}function Bt(e,t){return{...At(e,t.lights,t.id),...t}}function Vt(e,t){let n=e.states[t.sun_entity||`sun.sun`];if(!n)return null;if(n.state===`below_horizon`)return`dark`;if(n.state!==`above_horizon`)return null;let r=n.attributes.elevation,i=t.dusk_elevation??5;return typeof r==`number`&&r<i?`dusk`:`light`}function Ht(e,t){let n=e.states[t.sun_entity||`sun.sun`]?.attributes.elevation;return typeof n==`number`?n:null}var Ut={lights:!0,fans:!0,covers:!0,locks:!1,media:!0,vacuum:!0,switches:!0,maintenance:!0};function q(e,t,n,r){var i=arguments.length,a=i<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,n):r,o;if(typeof Reflect==`object`&&typeof Reflect.decorate==`function`)a=Reflect.decorate(e,t,n,r);else for(var s=e.length-1;s>=0;s--)(o=e[s])&&(a=(i<3?o(a):i>3?o(t,n,a):o(t,n))||a);return i>3&&a&&Object.defineProperty(t,n,a),a}var Wt=class extends R{constructor(...e){super(...e),this.checked=!1,this.disabled=!1,this.label=``}static{this.styles=[Me,o`
      :host {
        display: inline-flex;
        align-items: center;
        gap: var(--vr-space-2);
        cursor: pointer;
        user-select: none;
      }

      :host([disabled]) {
        opacity: 0.4;
        cursor: default;
        pointer-events: none;
      }

      .track {
        position: relative;
        width: 40px;
        height: 22px;
        border-radius: 11px;
        background: var(--vr-fill-strong);
        transition: background 0.18s ease;
        flex: none;
      }

      :host([checked]) .track,
      .track.on {
        background: var(--primary-color);
      }

      .thumb {
        position: absolute;
        top: 3px;
        left: 3px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: white;
        box-shadow: 0 1px 3px rgb(0 0 0 / 25%);
        transition: transform 0.18s ease;
      }

      :host([checked]) .thumb,
      .track.on .thumb {
        transform: translateX(18px);
      }

      .label-text {
        font-size: var(--vr-font-md);
        color: var(--primary-text-color);
      }
    `]}render(){return F`
      <div
        class="track ${this.checked?`on`:``}"
        role="switch"
        tabindex="0"
        aria-checked=${this.checked}
        aria-label=${this.label}
        @click=${this._toggle}
        @keydown=${this._onKeydown}
      >
        <div class="thumb"></div>
      </div>
      ${this.label?F`<span class="label-text">${this.label}</span>`:``}
    `}_toggle(){this.disabled||(this.checked=!this.checked,this.dispatchEvent(new CustomEvent(`change`,{detail:{value:this.checked},bubbles:!0})))}_onKeydown(e){(e.key===` `||e.key===`Enter`)&&(e.preventDefault(),this._toggle())}};q([z({type:Boolean})],Wt.prototype,`checked`,void 0),q([z({type:Boolean,reflect:!0})],Wt.prototype,`disabled`,void 0),q([z({type:String})],Wt.prototype,`label`,void 0),Wt=q([ke(`vr-toggle`)],Wt);var Gt=class extends R{constructor(...e){super(...e),this.entityId=``,this.size=28}static{this.styles=[Me,o`
      :host {
        display: inline-block;
        flex: none;
      }

      .avatar {
        position: relative;
        display: grid;
        place-items: center;
        border-radius: 50%;
        overflow: hidden;
        box-sizing: border-box;
        border: 2px solid var(--vr-border);
        background: var(--vr-fill-strong);
        color: var(--secondary-text-color);
        font-weight: 600;
        transition: border-color 0.2s ease, filter 0.2s ease, background 0.2s ease;
      }

      .avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .avatar.home {
        border-color: var(--vr-home);
        background: var(--vr-home-bg);
        color: var(--primary-text-color);
        box-shadow: 0 0 0 2px var(--vr-home-bg);
      }

      .avatar.away {
        filter: grayscale(1);
        opacity: 0.6;
      }
    `]}render(){let e=this.hass.states[this.entityId],t=e?.attributes.friendly_name??this.entityId,n=e?.attributes.entity_picture,r=e?.state===`home`,i=t.split(/\s+/).filter(Boolean).slice(0,2).map(e=>e[0]?.toUpperCase()).join(``),a=`${t}: ${V(r?`person.home`:`person.away`,this.hass.language)}`;return F`
      <span
        class="avatar ${r?`home`:`away`}"
        style="width:${this.size}px;height:${this.size}px;font-size:${Math.round(this.size*.4)}px"
        role="img"
        aria-label=${a}
        title=${a}
      >
        ${n?F`<img src=${n} alt="" />`:i}
      </span>
    `}};q([z({attribute:!1})],Gt.prototype,`hass`,void 0),q([z({attribute:!1})],Gt.prototype,`entityId`,void 0),q([z({type:Number})],Gt.prototype,`size`,void 0),Gt=q([ke(`vr-person-avatar`)],Gt);var J=class extends R{constructor(...e){super(...e),this.saveState=`idle`,this.rooms=[],this.textDefaults={},this._announceText=``,this._announceResult=null}static{this.styles=[Me,o`
      .mode-seg {
        display: inline-flex;
        border: 1px solid var(--vr-border-strong, var(--divider-color));
        border-radius: 16px;
        overflow: hidden;
        flex: none;
      }

      .mode-btn {
        font: inherit;
        font-size: var(--vr-font-sm, 13px);
        padding: 6px 12px;
        border: none;
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
      }

      .mode-btn.on {
        background: var(--vr-fill-primary, rgba(3, 169, 244, 0.12));
        color: var(--primary-color);
      }

      .mode-btn[disabled] {
        opacity: 0.5;
        cursor: default;
      }

      :host {
        display: block;
        padding: var(--vr-space-5);
        max-width: 720px;
        margin: 0 auto;
      }

      .back-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        margin-bottom: var(--vr-space-5);
      }

      .back-row ha-icon-button {
        --mdc-icon-button-size: 40px;
        --mdc-icon-size: 20px;
        color: var(--primary-text-color);
      }

      h1 {
        font-size: var(--vr-font-xl);
        font-weight: 500;
        color: var(--primary-text-color);
        margin: 0;
      }

      .save-status {
        margin-left: auto;
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .save-status.error {
        color: var(--error-color);
      }

      .section {
        margin-bottom: var(--vr-space-6);
      }

      .section-title {
        font-size: var(--vr-font-sm);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--secondary-text-color);
        margin: 0 0 var(--vr-space-2);
      }

      .hint {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        margin: 0 0 var(--vr-space-3);
      }

      .list {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
      }

      .late-chip {
        font: inherit;
        font-size: var(--vr-font-xs);
        display: inline-flex;
        align-items: center;
        gap: 4px;
        flex: none;
        min-height: 28px;
        padding: 2px 10px 2px 6px;
        border: 1px solid var(--vr-border);
        border-radius: 999px;
        background: var(--vr-surface);
        color: var(--secondary-text-color);
        cursor: pointer;
      }

      .late-chip ha-icon {
        --mdc-icon-size: 16px;
      }

      .late-chip.on {
        border-color: var(--primary-color);
        background: var(--vr-fill-primary);
        color: var(--primary-color);
      }

      .smoke-chip {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 4px 2px 10px;
        border: 1px solid var(--vr-border);
        border-radius: 999px;
        font-size: var(--vr-font-sm);
      }

      .txt-card {
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        margin-bottom: var(--vr-space-3);
      }

      .txt-grp {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px;
        padding: var(--vr-space-2) var(--vr-space-3);
        font-size: var(--vr-font-sm);
        font-weight: 500;
        color: var(--secondary-text-color);
      }

      .txt-grp .spacer {
        flex: 1;
      }

      .txt-ph-label {
        font-weight: 400;
      }

      .txt-ph {
        font-size: var(--vr-font-xs);
        padding: 1px 6px;
        border-radius: 4px;
        border: 1px solid var(--vr-border);
        font-weight: 400;
      }

      .txt-row {
        display: grid;
        grid-template-columns: minmax(110px, 170px) minmax(0, 1fr) 32px;
        gap: var(--vr-space-1) var(--vr-space-2);
        align-items: center;
        padding: var(--vr-space-2) var(--vr-space-3);
        border-top: 1px solid var(--vr-border);
      }

      .txt-label {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: var(--vr-font-sm);
      }

      .txt-label ha-icon,
      .txt-vol ha-icon {
        --mdc-icon-size: 16px;
        color: var(--secondary-text-color);
        flex: none;
      }

      .txt-input {
        width: 100%;
        min-width: 0;
        box-sizing: border-box;
      }

      .txt-input.own {
        border-color: var(--primary-color);
      }

      .txt-note {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .txt-reset {
        border: none;
        background: none;
        cursor: pointer;
        color: var(--secondary-text-color);
        display: inline-grid;
        place-items: center;
        padding: 4px;
      }

      .txt-reset ha-icon {
        --mdc-icon-size: 18px;
      }

      .txt-vol {
        grid-column: 2 / -1;
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .txt-vol input[type="range"] {
        flex: 1;
        max-width: 240px;
        min-width: 0;
      }

      .txt-vol input.unset {
        opacity: 0.45;
      }

      .txt-vol-val {
        min-width: 44px;
      }

      @media (max-width: 520px) {
        .txt-row {
          grid-template-columns: minmax(0, 1fr) 32px;
        }

        .txt-label,
        .txt-vol {
          grid-column: 1 / -1;
        }
      }

      .smoke-chip.on {
        border-color: var(--primary-color);
        color: var(--primary-color);
      }

      .smoke-chip-x {
        border: none;
        background: none;
        padding: 2px;
        cursor: pointer;
        color: var(--secondary-text-color);
        display: inline-flex;
      }

      .row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        min-height: 56px;
        padding: 0 var(--vr-space-4);
        cursor: pointer;
      }

      .row + .row {
        border-top: 1px solid var(--vr-border);
      }

      .row input {
        width: 18px;
        height: 18px;
        margin: 0;
        accent-color: var(--primary-color);
        flex: none;
      }

      .name {
        flex: 1;
        min-width: 0;
        font-size: var(--vr-font-md);
        color: var(--primary-text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .state {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .toggle-row {
        cursor: default;
      }

      .toggle-text {
        flex: 1;
      }

      .toggle-title {
        font-size: var(--vr-font-md);
        color: var(--primary-text-color);
      }

      .toggle-hint {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        margin-top: 2px;
      }

      .select {
        font: inherit;
        font-size: var(--vr-font-md);
        max-width: 55%;
        padding: 6px 8px;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        color: var(--primary-text-color);
      }

      .empty {
        padding: var(--vr-space-4);
        font-size: var(--vr-font-md);
        color: var(--secondary-text-color);
      }
    `]}_ph(e){return`{${this.hass.language.startsWith(`nl`)?{room:`ruimte`,name:`naam`,hours:`uren`}[e]??e:e}}`}_phText(e){return e.replace(/\{(room|name|hours)\}/g,(e,t)=>this._ph(t))}_renderTextGroup(e,t){let n=this.hass.language,r=this.settings.texts??{},i=this.settings.volumes??{},a=(e,t)=>{let n={...r,[e]:t.trim()};n[e]||delete n[e],this._emit({...this.settings,texts:Object.keys(n).length?n:void 0})},o=(e,t)=>{let n={...i};t===void 0?delete n[e]:n[e]=t,this._emit({...this.settings,volumes:Object.keys(n).length?n:void 0})},s=t.filter(e=>!e.key||this.textDefaults[e.key]);if(!s.length)return L;let c=[...new Set(s.flatMap(e=>e.key?this.textDefaults[e.key].placeholders:[]))];return F`
      <div class="txt-card">
        <div class="txt-grp">
          <span>${e}</span>
          <span class="spacer"></span>
          ${c.length?F`<span class="txt-ph-label">${V(`texts.placeholders`,n)}</span>
            ${c.map(e=>F`<code class="txt-ph">${this._ph(e)}</code>`)}`:L}
        </div>
        ${s.map(e=>{let t=e.key?r[e.key]??``:``,s=e.volume?i[e.volume]:void 0;return F`
            <div class="txt-row">
              <span class="txt-label">
                <ha-icon icon=${e.volume?`mdi:volume-high`:`mdi:bell-outline`}></ha-icon>${e.label}
              </span>
              ${e.key?F`
                <input class="select txt-input ${t?`own`:``}" .value=${this._phText(t)}
                  placeholder=${this._phText(this.textDefaults[e.key].text)} aria-label=${e.label}
                  @change=${t=>a(e.key,t.target.value)} />
                ${t?F`<button class="txt-reset" title=${V(`texts.reset`,n)} aria-label=${V(`texts.reset`,n)}
                  @click=${()=>a(e.key,``)}><ha-icon icon="mdi:restore"></ha-icon></button>`:F`<span></span>`}`:F`<span class="txt-note">${e.note??``}</span><span></span>`}
              ${e.volume?F`
                <div class="txt-vol">
                  <ha-icon icon=${s===void 0?`mdi:volume-off`:`mdi:volume-medium`}></ha-icon>
                  <input type="range" min="0" max="100" step="5" .value=${String(s??50)}
                    class=${s===void 0?`unset`:``}
                    aria-label="${V(`texts.volume`,n)}: ${e.label}"
                    @change=${t=>o(e.volume,Number(t.target.value))} />
                  <span class="txt-vol-val">${s===void 0?V(`texts.volume_own`,n):`${s}%`}</span>
                  ${s===void 0?L:F`<button class="txt-reset" title=${V(`texts.volume_clear`,n)}
                    aria-label=${V(`texts.volume_clear`,n)} @click=${()=>o(e.volume,void 0)}>
                    <ha-icon icon="mdi:close"></ha-icon></button>`}
                </div>`:L}
            </div>`})}
      </div>`}_renderTextsSection(){let e=this.hass.language;return Object.keys(this.textDefaults).length?F`
      <section class="section">
        <h2 class="section-title">${V(`texts.section`,e)}</h2>
        <p class="hint">${V(`texts.hint`,e)}</p>
        ${this._renderTextGroup(V(`texts.grp_doorbell`,e),[{key:`doorbell_spoken`,volume:`doorbell`,label:V(`texts.spoken`,e)},{key:`doorbell_notify`,label:V(`texts.notify`,e)}])}
        ${this._renderTextGroup(V(`texts.grp_alerts`,e),[{key:`anomaly_motion`,label:V(`texts.anomaly_motion`,e)},{key:`anomaly_lights_on`,label:V(`texts.anomaly_lights_on`,e)}])}
        ${this._renderTextGroup(V(`texts.grp_announce`,e),[{volume:`announce`,label:V(`texts.volume`,e),note:V(`texts.announce_note`,e)}])}
      </section>`:L}_announceTts(){let e=this.settings;return(`announce_tts`in e?e.announce_tts:e.smoke_tts)??``}_renderAnnounce(){let e=this.hass.language,t=e=>this.hass.states[e]?.attributes.friendly_name??e,n=Object.keys(this.hass.states).filter(e=>e.startsWith(`tts.`)).sort(),r=this._announceTts(),i=this.settings.persons??[],a=e=>this.hass.areas?.[e]?.name??e,o=this.rooms.filter(e=>!e.hidden||(e.media_players??[]).length>0).flatMap(n=>(n.media_players??[]).map(r=>{let o=(n.persons??[]).filter(e=>i.includes(e)),s=o.filter(e=>this.hass.states[e]?.state===`home`),c=(n.announce_off??[]).includes(r),l=c?`off`:o.length>0&&s.length===0?`away`:`on`,u=c?V(`announce.why_off`,e):o.length===0?V(`announce.why_no_persons`,e):s.length?V(`announce.why_home`,e).replace(`{names}`,s.map(t).join(`, `)):V(`announce.why_away`,e).replace(`{names}`,o.map(t).join(`, `));return{room:a(n.area_id),player:t(r),status:l,why:u}})),s=this.settings.announce_messages??[],c=this._announceText.trim(),l=()=>{c&&!s.includes(c)&&this._emit({...this.settings,announce_messages:[...s,c]})},u=e=>{let t=s.filter(t=>t!==e);this._emit({...this.settings,announce_messages:t.length?t:void 0})},d=async()=>{let t=this._announceText.trim();if(t)try{let n=await this.hass.callWS({type:`roomcontrol/announce`,message:t});this._announceResult=n.players.length?V(`announce.sent`,e).replace(`{n}`,String(n.players.length)):V(`announce.sent_none`,e)}catch{this._announceResult=V(`announce.failed`,e)}};return F`
      <section class="section">
        <h2 class="section-title">${V(`announce.section`,e)}</h2>
        <p class="hint">${V(`announce.hint`,e)}</p>
        <div class="list">
          <label class="row toggle-row">
            <ha-icon icon="mdi:account-voice" style="--mdc-icon-size:20px;color:${r?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
            <span class="toggle-text">
              <span class="toggle-title">${V(`announce.tts`,e)}</span>
              <span class="toggle-hint">${V(n.length?`announce.tts_hint`:`announce.tts_none`,e)}</span>
            </span>
            <select class="select" aria-label=${V(`announce.tts`,e)}
              @change=${e=>this._emit({...this.settings,announce_tts:e.target.value})}>
              <option value="" ?selected=${!r}>${V(`announce.tts_off`,e)}</option>
              ${n.map(e=>F`<option value=${e} ?selected=${r===e}>${t(e)}</option>`)}
            </select>
          </label>
          ${r?F`
            <div class="row toggle-row">
              <ha-icon icon="mdi:message-text-outline" style="--mdc-icon-size:20px;color:var(--secondary-text-color)"></ha-icon>
              <input class="select" style="flex: 1 1 auto; width: 0; min-width: 0"
                .value=${this._announceText} placeholder=${V(`announce.test_placeholder`,e)}
                aria-label=${V(`announce.test`,e)}
                @input=${e=>{this._announceText=e.target.value,this._announceResult=null}}
                @keydown=${e=>{e.key===`Enter`&&d()}} />
              ${c&&!s.includes(c)?F`
                <button class="select" style="flex: none; cursor: pointer" title=${V(`announce.save`,e)}
                  aria-label=${V(`announce.save`,e)} @click=${l}>
                  <ha-icon icon="mdi:bookmark-plus-outline" style="--mdc-icon-size:18px"></ha-icon></button>`:L}
              <button class="select" style="flex: none; cursor: pointer" @click=${()=>void d()}>${V(`announce.test`,e)}</button>
            </div>
            ${s.length?F`
              <div class="row" style="flex-wrap: wrap; gap: var(--vr-space-2)">
                ${s.map(t=>F`
                  <span class="smoke-chip ${t===c?`on`:``}">
                    <button class="smoke-chip-x" style="color: inherit; font: inherit; padding: 0"
                      title=${V(`announce.use`,e)}
                      @click=${()=>{this._announceText=t,this._announceResult=null}}>${t}</button>
                    <button class="smoke-chip-x" aria-label="${V(`common.remove`,e)}: ${t}" @click=${()=>u(t)}>
                      <ha-icon icon="mdi:close" style="--mdc-icon-size:14px"></ha-icon></button>
                  </span>`)}
              </div>`:L}
            ${this._announceResult?F`<p class="hint" style="margin: 0; padding: var(--vr-space-2) var(--vr-space-3)">${this._announceResult}</p>`:L}
          `:L}
        </div>
        <p class="hint" style="margin-top: var(--vr-space-3)">${V(`announce.now_title`,e)}</p>
        <div class="list">
          ${o.length===0?F`<p class="hint" style="margin: 0; padding: var(--vr-space-2) var(--vr-space-3)">${V(`announce.none`,e)}</p>`:L}
          ${o.map(t=>F`
            <div class="row toggle-row">
              <ha-icon icon="mdi:bullhorn-outline" style="--mdc-icon-size:20px;color:${t.status===`on`?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
              <div class="toggle-text">
                <div class="toggle-title">${t.room} · ${t.player}</div>
                <div class="toggle-hint">${t.why}</div>
              </div>
              <span class="toggle-hint" style="flex: none; color: ${t.status===`on`?`var(--success-color, #43a047)`:`var(--secondary-text-color)`}">
                ${V(`announce.status_${t.status}`,e)}</span>
            </div>`)}
        </div>
        <p class="hint">${V(`announce.service_hint`,e)}</p>
      </section>
    `}_renderSmoke(){let e=this.hass.language,t=this.settings.smoke_detectors??[],n=Object.keys(this.hass.states).filter(e=>e.startsWith(`binary_sensor.`)&&this.hass.states[e].attributes.device_class===`smoke`),r=[...new Set([...t,...n])].sort(),i=e=>this.hass.states[e]?.attributes.friendly_name??e,a={...Ut,...this.settings.smoke_actions??{}},o=(e,t)=>this._emit({...this.settings,smoke_actions:{...this.settings.smoke_actions??{},[e]:t}}),s=t=>{let n=this.hass.states[t];if(!n||n.state===`unavailable`||n.state===`unknown`)return{text:V(`smoke.offline`,e),cls:`warn`};if(n.state===`on`)return{text:V(`smoke.detected`,e),cls:`alert`};let r=bt(this.hass,t),i=r?this.hass.states[r]:void 0,a=i?r.startsWith(`binary_sensor.`)?i.state===`on`:Number(i.state)<20:!1,o=i&&!r.startsWith(`binary_sensor.`)&&!isNaN(Number(i.state))?`${Math.round(Number(i.state))}%`:``;return a?{text:`${V(`smoke.battery_low`,e)}${o?` · ${o}`:``}`,cls:`warn`}:{text:`${V(`smoke.clear_state`,e)}${o?` · ${V(`smoke.battery`,e)} ${o}`:``}`,cls:``}},c=[{k:`lights`,icon:`mdi:lightbulb-on`},{k:`fans`,icon:`mdi:fan-off`},{k:`covers`,icon:`mdi:blinds-open`},{k:`locks`,icon:`mdi:lock-open-variant-outline`},{k:`media`,icon:`mdi:speaker-message`},{k:`vacuum`,icon:`mdi:robot-vacuum-off`},{k:`switches`,icon:`mdi:power-plug-off-outline`},{k:`maintenance`,icon:`mdi:battery-alert-variant-outline`}],l=this.settings.smoke_switches??[],u=Object.keys(this.hass.states).filter(e=>e.startsWith(`switch.`)&&this.hass.entities?.[e]?.platform!==`roomcontrol`&&!l.includes(e)).sort((e,t)=>i(e).localeCompare(i(t))),d=e=>this._emit({...this.settings,smoke_switches:e});return F`
      <section class="section">
        <h2 class="section-title">${V(`smoke.section`,e)}</h2>
        <p class="hint">${V(`smoke.hint`,e)}</p>
        <div class="list">
          ${r.length===0?F`<p class="hint" style="margin:0;padding:var(--vr-space-2) var(--vr-space-3)">${V(`smoke.none`,e)}</p>`:L}
          ${r.map(e=>{let n=t.includes(e),r=s(e);return F`
              <div class="row toggle-row">
                <ha-icon icon=${r.cls===`alert`?`mdi:fire-alert`:`mdi:smoke-detector-variant`}
                  style="--mdc-icon-size:20px;color:${r.cls===`alert`?`var(--error-color, #db4437)`:r.cls===`warn`?`var(--warning-color, #ffa600)`:n?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
                <div class="toggle-text">
                  <div class="toggle-title">${i(e)}</div>
                  <div class="toggle-hint" style=${r.cls?`color:${r.cls===`alert`?`var(--error-color, #db4437)`:`var(--warning-color, #ffa600)`}`:``}>${r.text}</div>
                </div>
                <vr-toggle .checked=${n} .label=${``}
                  @change=${n=>this._emit({...this.settings,smoke_detectors:n.detail.value?[...t,e]:t.filter(t=>t!==e)})}></vr-toggle>
              </div>`})}
        </div>
        ${t.length>0?F`
          <p class="hint" style="margin-top:var(--vr-space-3)">${V(`smoke.actions_title`,e)}</p>
          <div class="list">
            ${c.map(t=>F`
              <div class="row toggle-row">
                <ha-icon icon=${t.icon} style="--mdc-icon-size:20px;color:${a[t.k]?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
                <div class="toggle-text">
                  <div class="toggle-title">${V(`smoke.action_${t.k}`,e)}</div>
                  <div class="toggle-hint">${V(`smoke.action_${t.k}_hint`,e)}</div>
                </div>
                <vr-toggle .checked=${a[t.k]} .label=${``} @change=${e=>o(t.k,e.detail.value)}></vr-toggle>
              </div>
              ${t.k===`switches`&&a.switches?F`
                <div class="row" style="flex-wrap: wrap; gap: var(--vr-space-2)">
                  ${l.map(t=>F`
                    <span class="smoke-chip">
                      <ha-icon icon="mdi:power-plug-outline" style="--mdc-icon-size:16px"></ha-icon>${i(t)}
                      <button class="smoke-chip-x" aria-label="${V(`common.remove`,e)}: ${i(t)}"
                        @click=${()=>d(l.filter(e=>e!==t))}>
                        <ha-icon icon="mdi:close" style="--mdc-icon-size:14px"></ha-icon></button>
                    </span>`)}
                  <select class="select" style="min-width: 0; max-width: 100%" aria-label=${V(`smoke.switches_add`,e)}
                    @change=${e=>{let t=e.target;t.value&&d([...l,t.value]),t.value=``}}>
                    <option value="" selected>${V(l.length?`smoke.switches_add`:`smoke.switches_pick`,e)}</option>
                    ${u.map(e=>F`<option value=${e}>${i(e)}</option>`)}
                  </select>
                </div>`:L}`)}
          </div>`:L}
        ${t.length>0&&Object.keys(this.textDefaults).length?F`
          ${this._renderTextGroup(V(`texts.grp_smoke`,e),[{key:`smoke_spoken`,volume:`smoke`,label:V(`texts.spoken`,e)},{key:`smoke_notify`,label:V(`texts.notify`,e)},{key:`smoke_battery`,label:V(`texts.smoke_battery_short`,e)},{key:`smoke_offline`,label:V(`texts.smoke_offline_short`,e)}])}`:L}
      </section>
    `}render(){let e=this.hass.language,t=Object.keys(this.hass.states).filter(e=>e.startsWith(`person.`)).sort((t,n)=>this._name(t).localeCompare(this._name(n),e)),n=Object.keys(this.hass.floors??{}).length;return F`
      <div class="back-row">
        <ha-icon-button
          .label=${V(`room.back`,e)}
          .path=${`M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z`}
          @click=${()=>this.dispatchEvent(new CustomEvent(`back`,{bubbles:!0,composed:!0}))}
        ></ha-icon-button>
        <h1>${V(`settings.title`,e)}</h1>
        <span class="save-status ${this.saveState}" role="status" aria-live="polite">
          ${this.saveState===`saving`?V(`room.saving`,e):this.saveState===`saved`?V(`room.saved`,e):this.saveState===`error`?V(`room.error_save`,e):L}
        </span>
      </div>

      <section class="section">
        <h2 class="section-title">${V(`settings.presence`,e)}</h2>
        <p class="hint">${V(`settings.presence_hint`,e)}</p>
        <div class="list">
          ${t.length===0?F`<div class="empty">${V(`settings.no_persons`,e)}</div>`:t.map(t=>{let n=this.hass.states[t]?.state===`home`;return F`
                  <label class="row">
                    <input
                      type="checkbox"
                      .checked=${this.settings.persons.includes(t)}
                      @change=${()=>this._togglePerson(t)}
                    />
                    <vr-person-avatar .hass=${this.hass} .entityId=${t} .size=${36}></vr-person-avatar>
                    <span class="name">${this._name(t)}</span>
                    <span class="state">${V(n?`person.home`:`person.away`,e)}</span>
                    ${this.settings.persons.includes(t)?F`
                      <button
                        class="late-chip ${(this.settings.late_home_persons??[]).includes(t)?`on`:``}"
                        role="checkbox"
                        aria-checked=${(this.settings.late_home_persons??[]).includes(t)?`true`:`false`}
                        title=${V(`settings.late_home`,e).replace(`{name}`,this._name(t))}
                        @click=${e=>{e.preventDefault(),e.stopPropagation(),this._toggleLateHome(t)}}
                      >
                        <ha-icon icon=${(this.settings.late_home_persons??[]).includes(t)?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
                        ${V(`settings.late_home_short`,e)}
                      </button>
                      <button
                        class="late-chip ${this._clockPerson(t)?`on`:``}"
                        role="checkbox"
                        aria-checked=${this._clockPerson(t)?`true`:`false`}
                        title=${V(`settings.clock_person`,e).replace(`{name}`,this._name(t))}
                        @click=${e=>{e.preventDefault(),e.stopPropagation(),this._toggleClockPerson(t)}}
                      >
                        <ha-icon icon=${this._clockPerson(t)?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
                        ${V(`settings.clock_person_short`,e)}
                      </button>
                      <button
                        class="late-chip ${this._vacuumPerson(t)?`on`:``}"
                        role="checkbox"
                        aria-checked=${this._vacuumPerson(t)?`true`:`false`}
                        title=${V(`settings.vacuum_person`,e).replace(`{name}`,this._name(t))}
                        @click=${e=>{e.preventDefault(),e.stopPropagation(),this._toggleVacuumPerson(t)}}
                      >
                        <ha-icon icon=${this._vacuumPerson(t)?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
                        ${V(`settings.vacuum_person_short`,e)}
                      </button>`:L}
                  </label>
                `})}
        </div>
      </section>

      <section class="section">
        <h2 class="section-title">${V(`settings.alarm`,e)}</h2>
        <p class="hint">${V(`settings.alarm_hint`,e)}</p>
        <div class="list">
          <label class="row toggle-row">
            <ha-icon icon="mdi:shield-home" style="--mdc-icon-size:20px;color:var(--secondary-text-color)"></ha-icon>
            <span class="toggle-text">
              <span class="toggle-title">${V(`settings.alarm_panel`,e)}</span>
            </span>
            <select
              class="select"
              aria-label=${V(`settings.alarm_panel`,e)}
              @change=${e=>this._emit({...this.settings,alarm_entity:e.target.value})}
            >
              <option value="" ?selected=${!this.settings.alarm_entity}>${V(`settings.alarm_none`,e)}</option>
              ${Object.keys(this.hass.states).filter(e=>e.startsWith(`alarm_control_panel.`)).sort().map(e=>F`<option value=${e} ?selected=${this.settings.alarm_entity===e}>
                  ${this.hass.states[e]?.attributes.friendly_name??e}
                </option>`)}
            </select>
          </label>
          <p class="hint" style="margin: 0; padding: var(--vr-space-2) var(--vr-space-3)">${V(`settings.alarm_fixed`,e)}</p>
        </div>
      </section>

      ${this._renderAnnounce()}

      ${this._renderSmoke()}

      ${this._renderTextsSection()}

      <section class="section">
        <h2 class="section-title">${V(`settings.sun`,e)}</h2>
        <p class="hint">${V(`settings.sun_hint`,e)}</p>
        <div class="list">
          <label class="row toggle-row">
            <ha-icon icon="mdi:weather-sunset" style="--mdc-icon-size:20px;color:var(--secondary-text-color)"></ha-icon>
            <span class="toggle-text">
              <span class="toggle-title">${V(`settings.sun_entity`,e)}</span>
              <span class="toggle-hint">${(()=>{let t=this.hass.states[this.settings.sun_entity||`sun.sun`]?.state;return V(t===`below_horizon`?`settings.sun_down`:t===`above_horizon`?`settings.sun_up`:`settings.sun_missing`,e)})()}</span>
            </span>
            <select
              class="select"
              aria-label=${V(`settings.sun_entity`,e)}
              @change=${e=>this._emit({...this.settings,sun_entity:e.target.value})}
            >
              ${(()=>{let e=Object.keys(this.hass.states).filter(e=>e.startsWith(`sun.`)).sort(),t=this.settings.sun_entity||`sun.sun`;return e.includes(t)||e.unshift(t),e.map(e=>F`<option value=${e} ?selected=${t===e}>
                  ${this.hass.states[e]?.attributes.friendly_name??e}
                </option>`)})()}
            </select>
          </label>
          <div class="row toggle-row">
            <ha-icon icon="mdi:weather-sunset-down" style="--mdc-icon-size:20px;color:var(--secondary-text-color)"></ha-icon>
            <span class="toggle-text">
              <span class="toggle-title">${V(`settings.dusk_elevation`,e)}</span>
              <span class="toggle-hint">${(()=>{let t=Ht(this.hass,this.settings),n=Vt(this.hass,this.settings);return t===null||n===null?V(`settings.sun_missing`,e):V(`settings.dusk_now`,e).replace(`{deg}`,t.toFixed(1)).replace(`{phase}`,V(`phase.${n}`,e))})()}</span>
            </span>
            <input type="range" min="0" max="10" step="1" style="width: 120px"
              aria-label=${V(`settings.dusk_elevation`,e)}
              .value=${String(this.settings.dusk_elevation??5)}
              @change=${e=>this._emit({...this.settings,dusk_elevation:Number(e.target.value)})} />
            <span class="toggle-title" style="min-width: 28px; text-align: right">${this.settings.dusk_elevation??5}°</span>
          </div>
        </div>
        <p class="hint">${V(`settings.dusk_hint`,e)}</p>
      </section>

      ${(()=>{let t=Object.keys(this.hass.states).find(e=>e.startsWith(`switch.`)&&this.hass.states[e].attributes.roomcontrol_vacation===!0),n=t?this.hass.states[t].state===`on`:!1;return F`
          <section class="section">
            <h2 class="section-title">${V(`settings.vacation`,e)}</h2>
            <div class="list">
              <div class="row toggle-row">
                <ha-icon icon="mdi:palm-tree" style="--mdc-icon-size:20px;color:${n?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
                <div class="toggle-text">
                  <div class="toggle-title">${V(`settings.vacation_title`,e)}</div>
                  <div class="toggle-hint">${V(t?n?`settings.vacation_on`:`settings.vacation_off`:`settings.vacation_missing`,e)}</div>
                </div>
                <span class="mode-seg" role="radiogroup" aria-label=${V(`settings.vacation_title`,e)}>
                  ${[!1,!0].map(r=>F`
                    <button class="mode-btn ${n===r?`on`:``}" role="radio" aria-checked=${n===r?`true`:`false`}
                      ?disabled=${!t}
                      @click=${()=>{t&&n!==r&&this.hass.callService(`switch`,r?`turn_on`:`turn_off`,{entity_id:t})}}>
                      ${V(r?`settings.mode_vacation`:`settings.mode_normal`,e)}
                    </button>`)}
                </span>
              </div>
              <div class="row toggle-row">
                <ha-icon icon="mdi:shield-airplane-outline" style="--mdc-icon-size:20px;color:${this.settings.vacation_follows_alarm?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
                <div class="toggle-text">
                  <div class="toggle-title">${V(`settings.vacation_alarm`,e)}</div>
                  <div class="toggle-hint">${this.settings.alarm_entity?V(this.settings.vacation_follows_alarm?`settings.vacation_alarm_on`:`settings.vacation_alarm_off`,e):V(`settings.vacation_alarm_no_panel`,e)}</div>
                </div>
                <vr-toggle
                  .checked=${!!this.settings.vacation_follows_alarm}
                  .label=${``}
                  ?disabled=${!this.settings.alarm_entity}
                  @change=${e=>this._emit({...this.settings,vacation_follows_alarm:e.detail.value})}
                ></vr-toggle>
              </div>
            </div>
          </section>`})()}

      <section class="section">
        <h2 class="section-title">${V(`settings.dim`,e)}</h2>
        <div class="list">
          <div class="row toggle-row">
            <ha-icon icon="mdi:brightness-4" style="--mdc-icon-size:20px;color:var(--secondary-text-color)"></ha-icon>
            <div class="toggle-text">
              <div class="toggle-title">${V(`settings.dim_level`,e)}</div>
              <div class="toggle-hint">${V(`settings.dim_level_hint`,e)}</div>
            </div>
            <input type="number" min="1" max="100" step="1" class="select" style="width: 72px"
              aria-label=${V(`settings.dim_level`,e)}
              .value=${String(this.settings.dim_level??1)}
              @change=${e=>{let t=e.target,n=Math.round(Math.min(100,Math.max(1,Number(t.value)||1)));t.value=String(n),this._emit({...this.settings,dim_level:n})}} />
            <span class="toggle-hint">%</span>
          </div>
        </div>
      </section>

      <section class="section">
        <h2 class="section-title">${V(`settings.display`,e)}</h2>
        <div class="list">
          <div class="row toggle-row">
            <ha-icon icon="mdi:floor-plan" style="--mdc-icon-size:20px;color:var(--secondary-text-color)"></ha-icon>
            <div class="toggle-text">
              <div class="toggle-title">${V(`settings.group_by_floor`,e)}</div>
              <div class="toggle-hint">
                ${V(n===0?`settings.no_floors`:`settings.group_by_floor_hint`,e)}
              </div>
            </div>
            <vr-toggle
              .checked=${this.settings.group_by_floor}
              .label=${``}
              @change=${e=>this._emit({...this.settings,group_by_floor:e.detail.value})}
            ></vr-toggle>
          </div>
        </div>
      </section>
    `}_vacuumPerson(e){return(this.settings.vacuum_persons??this.settings.persons).includes(e)}_toggleVacuumPerson(e){let t=(this.settings.vacuum_persons??this.settings.persons).filter(e=>this.settings.persons.includes(e)),n=t.includes(e)?t.filter(t=>t!==e):[...t,e];this._emit({...this.settings,vacuum_persons:n})}_clockPerson(e){return(this.settings.clock_persons??this.settings.persons).includes(e)}_toggleClockPerson(e){let t=(this.settings.clock_persons??this.settings.persons).filter(e=>this.settings.persons.includes(e)),n=t.includes(e)?t.filter(t=>t!==e):[...t,e];this._emit({...this.settings,clock_persons:n})}_toggleLateHome(e){let t=this.settings.late_home_persons??[],n=t.includes(e)?t.filter(t=>t!==e):[...t,e];this._emit({...this.settings,late_home_persons:n})}_name(e){return this.hass.states[e]?.attributes.friendly_name??e}_togglePerson(e){let t=this.settings.persons.includes(e)?this.settings.persons.filter(t=>t!==e):[...this.settings.persons,e];this._emit({...this.settings,persons:t})}_emit(e){this.dispatchEvent(new CustomEvent(`settings-changed`,{detail:{settings:e},bubbles:!0,composed:!0}))}};q([z({attribute:!1})],J.prototype,`hass`,void 0),q([z({attribute:!1})],J.prototype,`settings`,void 0),q([z({attribute:!1})],J.prototype,`saveState`,void 0),q([z({attribute:!1})],J.prototype,`rooms`,void 0),q([z({attribute:!1})],J.prototype,`textDefaults`,void 0),q([B()],J.prototype,`_announceText`,void 0),q([B()],J.prototype,`_announceResult`,void 0),J=q([ke(`vr-settings`)],J);var Kt=`1.17.1`,qt=class extends R{constructor(...e){super(...e),this.enabledPersons=[],this.links=[],this.phase=null}static{this.styles=[Me,o`
      :host {
        display: block;
        min-width: 0;
        height: 100%;
      }

      .card {
        min-width: 0;
        box-sizing: border-box;
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius);
        padding: var(--vr-space-4);
        cursor: pointer;
        transition: box-shadow 0.15s ease, border-color 0.15s ease;
        display: flex;
        flex-direction: column;
        gap: var(--vr-space-3);
        min-height: 168px;
        height: 100%;
      }

      .card.hidden {
        opacity: 0.55;
        border-style: dashed;
      }

      .hide-btn {
        flex: none;
        width: 32px;
        height: 32px;
        margin: -4px 0;
        display: grid;
        place-items: center;
        border: none;
        border-radius: 50%;
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
        opacity: 0.6;
      }

      .hide-btn:hover,
      .hide-btn:focus-visible {
        opacity: 1;
        background: var(--vr-fill);
      }

      .hide-btn ha-icon {
        --mdc-icon-size: 18px;
      }

      .status {
        flex: none;
        min-height: 24px;
        white-space: nowrap;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: var(--vr-font-sm);
        font-weight: 500;
        color: var(--secondary-text-color);
      }

      .card.manual {
        border-style: dashed;
        border-color: var(--primary-color);
      }

      .dim-btn.active {
        background: var(--vr-fill-primary);
        border-color: var(--primary-color);
        color: var(--primary-color);
      }

      .card:hover {
        box-shadow: var(--vr-shadow-pop);
        border-color: var(--vr-border-strong);
      }

      .card.on {
        border-color: color-mix(in srgb, var(--vr-on) 40%, var(--vr-border));
      }

      .top-row {
        display: flex;
        align-items: flex-start;
        gap: var(--vr-space-2);
      }

      /* Bulb lights up when any light in the room is on; glow follows brightness. */
      .bulb.on {
        color: var(--vr-on);
        background: color-mix(in srgb, var(--vr-on) 22%, transparent);
        box-shadow: 0 0 14px 2px color-mix(in srgb, var(--vr-on) var(--vr-glow, 60%), transparent);
      }

      .bulb.on .bulb-icon {
        filter: drop-shadow(0 0 4px color-mix(in srgb, var(--vr-on) 80%, transparent));
      }

      .room-name {
        font-size: var(--vr-font-lg);
        font-weight: 500;
        color: var(--primary-text-color);
        flex: 1;
        min-width: 0;
        /* long names wrap (max. two lines) instead of pushing the card wider */
        overflow-wrap: anywhere;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .sun-icon {
        --mdc-icon-size: 18px;
        flex: none;
        margin-top: 3px;
      }

      .sun-icon.dark {
        color: #7f77dd;
      }

      .sun-icon.dusk {
        color: #d85a30;
      }

      .sun-icon.light {
        color: var(--vr-on);
      }

      .vacuum-icon {
        --mdc-icon-size: 18px;
        flex: none;
        margin-top: 3px;
        color: var(--disabled-text-color, var(--secondary-text-color));
      }

      .vacuum-icon.today {
        color: var(--success-color, #43a047);
      }

      .state-icon {
        --mdc-icon-size: 18px;
        flex: none;
        margin-top: 3px;
        color: var(--secondary-text-color);
      }

      .state-icon.ok {
        color: var(--success-color, #43a047);
      }

      .state-icon.alert {
        color: var(--warning-color, #ffa600);
      }

      .state-icon.active {
        color: var(--primary-color);
      }

      .big-row {
        display: flex;
        align-items: baseline;
        gap: 6px;
        flex-wrap: wrap;
      }

      .big {
        font-size: 26px;
        font-weight: 500;
        line-height: 1.1;
        color: var(--primary-text-color);
        font-variant-numeric: tabular-nums;
      }

      .big.off {
        color: var(--secondary-text-color);
      }

      .level-bar {
        height: 4px;
        border-radius: 2px;
        background: var(--vr-fill);
        overflow: hidden;
      }

      .level-bar span {
        display: block;
        height: 100%;
        background: var(--vr-on);
        transition: width 0.3s ease;
      }

      .status-text {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .spacer {
        flex: 1;
      }

      .link-badge {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        font-size: var(--vr-font-xs);
        font-weight: 600;
        padding: 2px 8px 2px 6px;
        border-radius: 999px;
      }

      .link-badge ha-icon {
        --mdc-icon-size: 14px;
      }

      .link-badge.motion {
        background: color-mix(in srgb, var(--vr-motion) 16%, transparent);
        color: var(--primary-text-color);
      }

      .link-badge.fan {
        background: var(--vr-fill-primary);
        color: var(--primary-color);
      }

      .icon-btn {
        display: inline-grid;
        place-items: center;
        width: 34px;
        height: 34px;
        padding: 0;
        border: 1px solid var(--vr-border);
        border-radius: 50%;
        background: var(--vr-surface);
        color: var(--secondary-text-color);
        cursor: pointer;
        flex: none;
      }

      .icon-btn ha-icon {
        --mdc-icon-size: 18px;
      }

      .icon-btn:hover {
        border-color: var(--vr-border-strong);
      }

      .icon-btn.active {
        border-color: var(--primary-color);
        background: var(--vr-fill-primary);
        color: var(--primary-color);
      }

      .bottom-row {
        margin-top: auto; /* stays at the bottom of an equal-height card */
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        flex-wrap: wrap;
      }

      .light-count {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        flex: 1 0 auto;
      }

      .badge {
        font-size: var(--vr-font-xs);
        font-weight: 500;
        padding: 2px 8px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        gap: 3px;
        max-width: 100%;
        white-space: nowrap;
      }

      .badge ha-icon {
        --mdc-icon-size: 12px;
      }

    `]}updated(){let e=gt(this.hass,this.room.area_id)!==null;e&&this._tick===void 0?this._tick=window.setInterval(()=>this.requestUpdate(),1e3):!e&&this._tick!==void 0&&(window.clearInterval(this._tick),this._tick=void 0)}disconnectedCallback(){super.disconnectedCallback(),window.clearInterval(this._tick),this._tick=void 0}_renderStateIcons(){let e=this.hass.language,t=e=>this.hass.states[e]?.attributes.friendly_name??e,n=G(this.hass,this.room.area_id),r=[],i=n?.attributes.clock_next,a=n?.attributes.clock_ringing===!0;if(a||i){let t=i?new Date(i).toLocaleString(e,{weekday:`short`,hour:`2-digit`,minute:`2-digit`}):``;r.push(F`<ha-icon class="state-icon ${a?`alert`:`active`}"
        icon=${a?`mdi:alarm-bell`:`mdi:alarm`}
        title=${a?V(`card.clock_ringing`,e):V(`card.clock_next`,e).replace(`{when}`,t)}></ha-icon>`)}let o=(this.room.locks??[]).map(e=>e.entity_id).filter(e=>this.hass.states[e]);if(o.length){let n=o.filter(e=>this.hass.states[e].state===`unlocked`||this.hass.states[e].state===`open`),i=o.filter(e=>[`jammed`,`unavailable`,`unknown`].includes(this.hass.states[e].state)),a=n.length?V(`card.lock_open`,e).replace(`{names}`,n.map(t).join(`, `)):i.length?V(`card.lock_problem`,e).replace(`{names}`,i.map(t).join(`, `)):V(`card.lock_locked`,e);r.push(F`<ha-icon class="state-icon ${n.length||i.length?`alert`:`ok`}"
        icon=${n.length?`mdi:lock-open-variant`:i.length?`mdi:lock-alert`:`mdi:lock`}
        title=${a}></ha-icon>`)}let s=(this.room.door_sensors??[]).filter(e=>this.hass.states[e]);if(s.length){let n=s.filter(e=>this.hass.states[e].state===`on`);r.push(F`<ha-icon class="state-icon ${n.length?`alert`:``}"
        icon=${n.length?`mdi:door-open`:`mdi:door-closed`}
        title=${n.length?V(`card.door_open`,e).replace(`{names}`,n.map(t).join(`, `)):V(`card.door_closed`,e)}></ha-icon>`)}return r}render(){let e=this.hass.language,t=gt(this.hass,this.room.area_id),n=ut(this.hass,this.room,this.enabledPersons),r=mt(this.hass,this.room.area_id),i=this.room.lights.length,a=(this.room.groups??[]).length,o=a>0?`${a} ${V(a===1?`card.bundle`:`card.bundles`,e)}`:`${i} ${V(i===1?`card.lights`:`card.lights_plural`,e)}`,s=n.any_on&&n.avg_brightness!==null?Math.round(n.avg_brightness/255*100):null;return F`
      <div class="card ${n.any_on?`on`:``} ${this.room.hidden?`hidden`:``} ${t===null?``:`manual`}" @click=${this._openRoom}>
        <div class="top-row">
          <span class="room-name">${this.room.name}</span>
          ${(this.room.vacuums??[]).length===0?L:(()=>{let t=G(this.hass,this.room.area_id)?.attributes.vacuumed_at,n=t?new Date(t):null,r=new Date,i=!!n&&n.getFullYear()===r.getFullYear()&&n.getMonth()===r.getMonth()&&n.getDate()===r.getDate();return F`<ha-icon class="vacuum-icon ${i?`today`:``}" icon="mdi:robot-vacuum"
              title=${V(i?`card.vacuumed_today`:`card.vacuum_not_today`,e)}></ha-icon>`})()}
          ${this._renderStateIcons()}
          ${this.phase===null?L:F`<ha-icon
            class="sun-icon ${this.phase}"
            icon=${this.phase===`dark`?`mdi:weather-night`:this.phase===`dusk`?`mdi:weather-sunset-down`:`mdi:white-balance-sunny`}
            title=${V(this.phase===`dark`?`card.sun_down`:this.phase===`dusk`?`card.sun_dusk`:`card.sun_up`,e)}
          ></ha-icon>`}
          <button
            class="hide-btn"
            title=${this.room.hidden?V(`card.unhide`,e):V(`card.hide`,e)}
            aria-label=${this.room.hidden?V(`card.unhide`,e):V(`card.hide`,e)}
            @click=${this._toggleHidden}
          >
            <ha-icon icon=${this.room.hidden?`mdi:eye`:`mdi:eye-off-outline`}></ha-icon>
          </button>
        </div>

        <div class="big-row">
          <span class="big ${n.any_on?``:`off`}">${n.any_on?s===null?V(`card.on`,e):`${s}%`:V(`card.off`,e)}</span>
          <span class="light-count">· ${o}</span>
        </div>
        <div class="level-bar" role="presentation"><span style="width: ${n.any_on?s??100:0}%"></span></div>

        <div class="bottom-row">
          <span class="status-text">${n.status===`active`?V(`status.active`,e):V(`status.standby`,e)}</span>
          ${this.links.map(t=>F`<span class="link-badge ${t.kind}"
            title=${V(t.kind===`motion`?`card.link_motion`:`card.link_fan`,e).replace(`{n}`,String(t.n))}>
            <ha-icon icon=${t.kind===`motion`?`mdi:link-variant`:`mdi:fan`}></ha-icon>${t.n}
          </span>`)}
          <span class="spacer"></span>
          ${i>0?F`
            <button
              class="icon-btn ${t===null?``:`active`}"
              aria-pressed=${t!==null}
              aria-label=${t===null?V(`manual.start`,e):`${V(`manual.stop`,e)} (${_t(t)})`}
              title=${t===null?V(`manual.start`,e):`${V(`manual.stop`,e)} · ${_t(t)}`}
              @click=${this._toggleManual}
            ><ha-icon icon="mdi:hand-back-right-outline"></ha-icon></button>
            <button
              class="icon-btn ${r?`active`:``}"
              aria-pressed=${r}
              aria-label=${V(r?`dim.restore`:`dim.to_1`,e)}
              title=${V(r?`dim.restore`:`dim.to_1`,e)}
              @click=${this._toggleDim}
            ><ha-icon icon="mdi:brightness-4"></ha-icon></button>
          `:L}
        </div>
      </div>
    `}_openRoom(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent(`open-room`,{detail:{areaId:this.room.area_id},bubbles:!0,composed:!0}))}_toggleManual(e){e.stopPropagation();let t=gt(this.hass,this.room.area_id)!==null;this.dispatchEvent(new CustomEvent(`set-manual`,{detail:{areaId:this.room.area_id,minutes:t?0:void 0},bubbles:!0,composed:!0}))}_toggleDim(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent(`set-dim`,{detail:{areaId:this.room.area_id,dim:!mt(this.hass,this.room.area_id)},bubbles:!0,composed:!0}))}_toggleHidden(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent(`set-hidden`,{detail:{hidden:!this.room.hidden},bubbles:!0,composed:!0}))}};q([z({attribute:!1})],qt.prototype,`hass`,void 0),q([z({attribute:!1})],qt.prototype,`room`,void 0),q([z({attribute:!1})],qt.prototype,`enabledPersons`,void 0),q([z({attribute:!1})],qt.prototype,`links`,void 0),q([z({attribute:!1})],qt.prototype,`phase`,void 0),qt=q([ke(`vr-room-card`)],qt);var Jt=6e4;async function Yt(e,t,n,r,i){return t.length===0?{}:e.callWS({type:`history/history_during_period`,start_time:new Date(n).toISOString(),end_time:new Date(r).toISOString(),entity_ids:t,minimal_response:!i,no_attributes:!i,significant_changes_only:!1})}async function Xt(e,t,n,r,i=[]){let a=[...new Set(t.filter(Boolean))],o=a.filter(e=>i.includes(e)),s=a.filter(e=>!i.includes(e)),[c,l]=await Promise.all([Yt(e,s,n,r,!1),Yt(e,o,n,r,!0)]),u={...c,...l},d={};for(let e of a){let t;d[e]=(u[e]??[]).map(e=>(e.a&&(t=e.a),{state:e.s,t:e.lu*1e3,...t?{attrs:t}:{}})).sort((e,t)=>e.t-t.t)}return d}function Zt(e,t){let n=Math.round(e/Jt),r=Math.floor(n/60),i=n%60;return r===0?`${i} min`:i===0?`${r} ${t}`:`${r} ${t} ${i} min`}function Qt(e,t){let n;for(let r of e)if(r.t<=t)n=r.state;else break;return n}function $t(e,t,n){let r=new Set([t,n]);for(let i of e)for(let e of i)e.t>t&&e.t<n&&r.add(e.t);return[...r].sort((e,t)=>e-t)}function en(e,t){let n=[];for(let r=0;r<e.length-1;r++){let[i,a]=[e[r],e[r+1]];if(a<=i||!t(i))continue;let o=n[n.length-1];o&&o[1]===i?o[1]=a:n.push([i,a])}return n}function tn(e){return e.reduce((e,[t,n])=>e+(n-t),0)}function nn(e,t){let n=0,r=0;for(let[i,a]of e){for(;r<t.length&&t[r][1]<=i;)r++;for(let e=r;e<t.length&&t[e][0]<a;e++)n+=Math.max(0,Math.min(a,t[e][1])-Math.max(i,t[e][0]))}return n}function rn(e,t,n){if(e.length===0)return null;if(!t)return e[0];let r=Number(Qt(t,n));if(!Number.isFinite(r))return e[0];let i=Math.round(r);return i>=1&&i<=e.length?e[i-1]:null}function an(e,t,n){return t.map(t=>({t,lux:n(e.map(e=>Number(Qt(e,t))).filter(e=>Number.isFinite(e)))}))}var on,sn=36e5,cn=24*sn,Y=class extends R{static{on=this}constructor(...e){super(...e),this.sunEntity=`sun.sun`,this._period=`24h`,this._historyDays=10,this._data=null,this._loading=!1,this._error=!1,this._picked=null,this._debug=[],this._tall=!1,this._hoverT=null,this._hidden=new Set,this._zoom=1,this._viewH=typeof window<`u`?window.innerHeight:800,this._boxW=660,this._onWinResize=()=>{this._viewH=window.innerHeight},this._loadedKey=``,this._request=0}connectedCallback(){super.connectedCallback(),this._loadRetention(),window.addEventListener(`resize`,this._onWinResize),this._resize=new ResizeObserver(e=>{let t=e[0]?.contentRect.width;t&&Math.abs(t-this._boxW)>4&&(this._boxW=t)}),this._resize.observe(this)}disconnectedCallback(){window.removeEventListener(`resize`,this._onWinResize),this._resize?.disconnect(),super.disconnectedCallback()}_hours(e=this._period){return e===`24h`?24:e===`3d`?72:e===`7d`?168:this._historyDays*24}get _key(){let e=this.room;return[this._period,this._historyDays,e.lights.map(e=>e.entity_id).join(`,`),(e.schedules??[]).join(`,`),e.schedule_selector??``,at(e).join(`,`),e.lux_mode??``,this.sunEntity].join(`|`)}async _loadRetention(){try{let e=await this.hass.callWS({type:`roomcontrol/get_config`});typeof e.history_days==`number`&&e.history_days>0&&(this._historyDays=e.history_days)}catch{}}willUpdate(e){(e.has(`room`)||e.has(`_period`)||e.has(`hass`)||e.has(`_historyDays`))&&this.hass&&this.room&&this._key!==this._loadedKey&&this._load()}async _load(){this._loadedKey=this._key;let e=++this._request,t=this.room,n=t.lights.map(e=>e.entity_id);if(this._picked=null,n.length===0)this._data=null;else{this._loading=!0,this._error=!1;try{let r=Date.now(),i=r-this._hours()*sn,a=(t.schedules??[]).filter(Boolean),o=t.schedule_selector||``,s=at(t),c=this.sunEntity||`sun.sun`,l=await Xt(this.hass,[...n,...a,o,...s,c],i,r);if(e!==this._request)return;let u=n.map(e=>l[e]??[]),d=a.map(e=>l[e]??[]),f=o?l[o]??[]:null,p=s.map(e=>l[e]??[]),m=l[c]??[],h=$t([...u,...d,f??[],...p,m],i,r),g=en(h,e=>u.some(t=>Qt(t,e)===`on`)),_=[];for(let e=0;e<h.length-1;e++){let[t,n]=[h[e],h[e+1]],r=rn(a,f,t);if(!r||Qt(l[r]??[],t)!==`on`)continue;let i=this.hass.states[r]?.attributes.friendly_name??r,o=_[_.length-1];o&&o.iv[1]===t&&o.name===i?o.iv[1]=n:_.push({iv:[t,n],name:i})}let v=en(h,e=>Qt(m,e)===`below_horizon`),y=m.filter((e,t)=>e.state===`below_horizon`&&t>0&&m[t-1].state===`above_horizon`&&e.t>=i).map(e=>e.t),b=s.length?an(p,h,e=>st(e,t.lux_mode)):[];this._data={start:i,end:r,light:g,schedule:_,sunDown:v,lux:b,sunsets:y},this._loadDebug()}catch{e===this._request&&(this._error=!0)}finally{e===this._request&&(this._loading=!1)}}}async _loadDebug(){try{let e=await this.hass.callWS({type:`roomcontrol/get_debug`,area_id:this.room.area_id});this._debug=e.entries??[]}catch{this._debug=[]}}render(){let e=this.hass.language;if(this.room.lights.length===0)return F`<p class="hint">${V(`analysis.no_lights`,e)}</p>`;let t=[`24h`,`3d`,`7d`,`max`],n=t=>t===`max`?V(`analysis.period_max`,e).replace(`{n}`,String(this._historyDays)):V(`analysis.period_${t}`,e);return F`
      <div class="top">
        <div class="periods" role="group" aria-label=${V(`analysis.period`,e)}>
          ${t.filter(e=>e===`max`||this._hours(e)<this._historyDays*24).map(e=>F`
            <button aria-pressed=${this._period===e?`true`:`false`} @click=${()=>{this._period=e}}>${n(e)}</button>`)}
        </div>
        <span class="hint">${V(`analysis.kept`,e).replace(`{n}`,String(this._historyDays))}</span>
      </div>
      ${this._error?F`<p class="hint">${V(`analysis.load_error`,e)}</p>`:this._data?this._renderBody(this._data):F`<p class="hint">${V(`panel.loading`,e)}</p>`}
    `}_renderBody(e){let t=this.hass.language,n=V(`analysis.hour_short`,t),r=tn(e.light),i=e.schedule.map(e=>e.iv),a=tn(i),o=nn(e.light,i),s=a>0?Math.round(o/a*100):null,c=(this.room.schedules??[]).length>0;return F`
      <div class="tiles">
        ${this._tile(V(`analysis.light_on`,t),Zt(r,n))}
        ${c?this._tile(V(`analysis.schedule_on`,t),Zt(a,n)):L}
        ${c?this._tile(V(`analysis.on_in_schedule`,t),s===null?`—`:`${s}%`):L}
        ${c?this._tile(V(`analysis.on_outside`,t),Zt(r-o,n)):L}
      </div>
      ${this._loading?F`<p class="hint">${V(`panel.loading`,t)}</p>`:L}
      <div class="chart-tools">
        <button class="tool-btn ${this._tall?`active`:``}" aria-pressed=${this._tall?`true`:`false`}
          title=${V(this._tall?`analysis.smaller`:`analysis.taller`,t)}
          @click=${()=>{this._tall=!this._tall}}>
          <ha-icon icon=${this._tall?`mdi:arrow-collapse-vertical`:`mdi:arrow-expand-vertical`}></ha-icon>
          ${V(this._tall?`analysis.smaller`:`analysis.taller`,t)}
        </button>
        <label class="zoom">
          <ha-icon icon="mdi:magnify-minus-outline"></ha-icon>
          <input type="range" min="1" max="8" step="0.5" .value=${String(this._zoom)}
            aria-label=${V(`analysis.zoom`,t)}
            @input=${e=>{this._zoom=Number(e.target.value)}} />
          <ha-icon icon="mdi:magnify-plus-outline"></ha-icon>
          <span class="zoom-val">${this._zoom}×</span>
        </label>
      </div>
      <div class="chart-scroll">${this._renderChart(e)}</div>
      ${this._zoom>1?F`<p class="hint" style="margin-top: 4px">${V(`analysis.scroll_hint`,t)}</p>`:L}
      <div class="legend">
        ${[...e.lux.length?[[`lux`,`analysis.lg_lux`]]:[],...this._target()>0&&e.lux.length?[[`target`,`analysis.lg_target`]]:[],[`light`,`analysis.lg_light`],...c?[[`sched`,`analysis.lg_schedule`]]:[],[`sun`,`analysis.lg_sun`]].map(([e,n])=>F`
          <button class="lg ${this._hidden.has(e)?`off`:``}" aria-pressed=${this._hidden.has(e)?`false`:`true`}
            @click=${()=>{let t=new Set(this._hidden);t.has(e)?t.delete(e):t.add(e),this._hidden=t}}>
            <i class="dot ${e}"></i>${V(n,t)}
          </button>`)}
      </div>
      ${this._picked!==null&&e.light[this._picked]?this._renderPicked(e,e.light[this._picked],i):F`<p class="hint">${V(`analysis.tap_block`,t)}</p>`}
    `}_tile(e,t){return F`<div class="tile"><span class="tile-value">${t}</span><span class="tile-label">${e}</span></div>`}_target(){let e=this.room;return e.target_lux_enabled===!1?0:Number(e.target_lux)||0}static _smooth(e){if(!e.length)return``;let t=`M${e[0][0].toFixed(1)},${e[0][1].toFixed(1)}`;for(let n=1;n<e.length;n++){let[r,i]=e[n-1],[a,o]=e[n],s=(r+a)/2;t+=` C${s.toFixed(1)},${i.toFixed(1)} ${s.toFixed(1)},${o.toFixed(1)} ${a.toFixed(1)},${o.toFixed(1)}`}return t}_renderChart(e){let t=this.hass.language,n=e=>!this._hidden.has(e),r=Math.round(660*this._zoom),i=r-28,a=r/Math.max(200,this._boxW*this._zoom),o=Math.max(160,Math.round(this._viewH*(this._tall?.7:.4))),s=22+Math.round(o*a),c=s+24,l=s-22,u=Math.max(1,e.end-e.start),d=t=>56+(Math.min(e.end,Math.max(e.start,t))-e.start)/u*(i-56),f=this._target(),p=e.lux.map(e=>e.lux).filter(e=>e!==null),m=Math.max(f*1.2,p.length?Math.max(...p)*1.1:0,50)/4,h=10**Math.floor(Math.log10(m)),g=[1,2,2.5,5,10].map(e=>e*h).find(e=>e>=m)??m,_=g*4,v=e=>s-e/_*l,y=new Intl.NumberFormat(t,{maximumFractionDigits:0}),b=e.lux.filter(e=>e.lux!==null).map(e=>[d(e.t),v(e.lux)]);b.length&&b.push([d(e.end),b[b.length-1][1]]);let x=Math.max(6,l*.06),S=[],C=(e.end-e.start)/sn;if(C<=30){let n=new Date(e.start);n.setMinutes(0,0,0);for(let r=n.getTime()+sn;r<e.end;r+=sn)new Date(r).getHours()%(this._zoom>=4?1:this._zoom>=2?3:6)==0&&S.push({t:r,label:new Date(r).toLocaleTimeString(t,{hour:`2-digit`,minute:`2-digit`})})}else{let n=new Date(e.start);n.setHours(0,0,0,0);let r=C>336&&this._zoom<2?3:1;for(let i=n.getTime()+cn;i<e.end;i+=cn*r)S.push({t:i,label:new Date(i).toLocaleDateString(t,{weekday:`short`,day:`numeric`})})}let ee=e=>new Date(e).toLocaleTimeString(t,{hour:`2-digit`,minute:`2-digit`}),w=t=>{let n=t.currentTarget.getBoundingClientRect(),a=(t.clientX-n.left)/n.width*r;this._hoverT=a<56||a>i?null:e.start+(a-56)/(i-56)*u},T=this._hoverT;return F`<div class="plot-wrap" style="width: ${this._zoom*100}%">
      <svg class="chart" viewBox="0 0 ${r} ${c}" role="img" aria-label=${V(`analysis.chart_label`,t)}
        @pointermove=${w} @pointerleave=${()=>{this._hoverT=null}}>
        <text class="axis" x=${56} y=${14}>${V(`analysis.lg_lux`,t)}</text>
        ${[0,1,2,3,4].map(e=>I`
          <line class="grid" x1=${56} x2=${i} y1=${v(g*e)} y2=${v(g*e)}></line>
          <text class="axis" x=${50} y=${v(g*e)+3} text-anchor="end">${y.format(g*e)} lx</text>`)}
        ${n(`sun`)?e.sunDown.map(([e,t])=>I`<rect class="sun" x=${d(e)} y=${22} width=${Math.max(0,d(t)-d(e))} height=${l}></rect>`):L}
        ${n(`sched`)&&(this.room.schedules??[]).length?e.schedule.map(e=>I`<rect class="sched" x=${d(e.iv[0])} y=${22}
          width=${Math.max(1,d(e.iv[1])-d(e.iv[0]))} height=${x}><title>${e.name}</title></rect>`):L}
        ${n(`target`)&&f>0&&b.length?I`
          <rect class="target-band" x=${56} y=${v(Math.min(_,f*1.1))} width=${i-56} height=${Math.max(0,v(f*.9)-v(Math.min(_,f*1.1)))}></rect>
          <line class="target" x1=${56} x2=${i} y1=${v(f)} y2=${v(f)}></line>`:L}
        ${n(`lux`)&&b.length?I`<path class="lux" d=${on._smooth(b)}></path>`:L}
        ${n(`light`)?e.light.map(([e,t],n)=>I`<rect class="light ${this._picked===n?`picked`:``}" x=${d(e)} y=${s-x}
          width=${Math.max(1.5,d(t)-d(e))} height=${x} tabindex="0" role="button"
          aria-label=${`${ee(e)}–${ee(t)}`}
          @click=${()=>{this._picked=this._picked===n?null:n}}
          @keydown=${e=>{(e.key===`Enter`||e.key===` `)&&(e.preventDefault(),this._picked=n)}}></rect>`):L}
        ${Date.now()-e.end<6e5?I`<line class="now" x1=${d(e.end)} x2=${d(e.end)} y1=${22} y2=${s}></line>`:L}
        ${S.map(e=>I`<text class="axis" x=${d(e.t)} y=${s+16} text-anchor="middle">${e.label}</text>`)}
        ${T===null?L:I`<line class="cross" x1=${d(T)} x2=${d(T)} y1=${22} y2=${s}></line>`}
      </svg>
      ${T===null?L:this._renderTip(e,T,d(T)/r*100)}
    </div>`}_renderTip(e,t,n){let r=this.hass.language,i=e=>e.some(([e,n])=>t>=e&&t<n),a=e.lux.filter(e=>e.t<=t).pop()?.lux,o=e.schedule.find(e=>t>=e.iv[0]&&t<e.iv[1]),s=new Date(t).toLocaleString(r,e.end-e.start>30*sn?{weekday:`short`,day:`numeric`,hour:`2-digit`,minute:`2-digit`}:{hour:`2-digit`,minute:`2-digit`}),c=i(e.light);return F`<div class="tip ${n>60?`flip`:``}" style="left: ${n}%">
      <div class="tip-time">${s}</div>
      ${a==null?L:F`<div class="tip-row"><i class="dot lux"></i>${Math.round(a)} lx</div>`}
      ${this._target()>0?F`<div class="tip-row sub"><i class="dot target"></i>${V(`analysis.lg_target`,r)} ${this._target()} lx</div>`:L}
      <div class="tip-sep"></div>
      <div class="tip-row"><i class="dot light"></i>${V(c?`analysis.tip_light_on`:`analysis.tip_light_off`,r)}</div>
      ${(this.room.schedules??[]).length?F`<div class="tip-row sub"><i class="dot sched"></i>${o?o.name:V(`analysis.tip_sched_off`,r)}</div>`:L}
      <div class="tip-row sub"><i class="dot sun"></i>${V(i(e.sunDown)?`analysis.tip_sun_down`:`analysis.tip_sun_up`,r)}</div>
    </div>`}_renderPicked(e,t,n){let r=this.hass.language,i=t=>new Date(t).toLocaleString(r,e.end-e.start>30*sn?{weekday:`short`,hour:`2-digit`,minute:`2-digit`}:{hour:`2-digit`,minute:`2-digit`}),a=nn([t],n),o=n.length===0?``:a>=(t[1]-t[0])*.9?V(`analysis.in_schedule`,r):V(a>0?`analysis.partly_schedule`:`analysis.outside_schedule`,r),s=e=>Math.abs(new Date(e.at).getTime()-t[0])<2e4,c=this._debug.find(e=>e.kind===`on`&&s(e))??this._debug.find(e=>e.kind===`info`&&e.reason===`external_on`&&s(e)),l=c?((e,t)=>{let n=V(e,r);return n===e?t:n})(`debug.reason.${c.reason.replace(/[^a-z0-9_]+/gi,`_`).toLowerCase()}`,c.reason):``,u=e.lux.filter(e=>e.t<=t[0]).pop()?.lux;return F`<div class="picked">
      <strong>${i(t[0])} – ${i(t[1])}</strong> · ${Zt(t[1]-t[0],V(`analysis.hour_short`,r))}${o?` · ${o}`:``}
      <br />${c?F`${c.bundles.length?F`${c.bundles.join(`, `)} · `:L}${l}${u==null?``:` · ${Math.round(u)} lx`}`:V(`analysis.no_reason`,r)}
    </div>`}static{this.styles=[Me,o`
      :host { display: block; }
      .top { display: flex; align-items: center; justify-content: space-between; gap: var(--vr-space-2); flex-wrap: wrap; margin-bottom: var(--vr-space-3); }
      .periods { display: inline-flex; border: 1px solid var(--vr-border); border-radius: var(--vr-radius-sm); overflow: hidden; }
      .periods button { font: inherit; font-size: var(--vr-font-sm); padding: 6px 12px; border: none; background: none; color: var(--secondary-text-color); cursor: pointer; min-height: 32px; }
      .periods button + button { border-left: 1px solid var(--vr-border); }
      .periods button[aria-pressed="true"] { background: var(--vr-fill-primary); color: var(--primary-color); font-weight: 500; }
      .hint { font-size: var(--vr-font-sm); color: var(--secondary-text-color); margin: var(--vr-space-2) 0 0; }
      .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: var(--vr-space-2); margin-bottom: var(--vr-space-3); }
      .tile { background: var(--vr-surface); border: 1px solid var(--vr-border); border-radius: var(--vr-radius-sm); padding: var(--vr-space-2) var(--vr-space-3); display: flex; flex-direction: column; gap: 2px; }
      .tile-value { font-size: var(--vr-font-lg); font-weight: 500; font-variant-numeric: tabular-nums; }
      .tile-label { font-size: var(--vr-font-xs); color: var(--secondary-text-color); }
      .chart { display: block; height: auto; overflow: visible; max-width: none; }
      .chart-scroll { overflow-x: auto; overflow-y: hidden; padding-bottom: 4px; }
      .chart-tools { display: flex; align-items: center; justify-content: space-between; gap: var(--vr-space-3); flex-wrap: wrap; margin-bottom: var(--vr-space-2); }
      .tool-btn { font: inherit; font-size: var(--vr-font-sm); display: inline-flex; align-items: center; gap: 4px; min-height: 32px; padding: 4px 10px;
        border: 1px solid var(--vr-border); border-radius: var(--vr-radius-sm); background: var(--vr-surface); color: var(--secondary-text-color); cursor: pointer; }
      .tool-btn ha-icon, .zoom ha-icon { --mdc-icon-size: 18px; }
      .tool-btn.active { border-color: var(--primary-color); color: var(--primary-color); background: var(--vr-fill-primary); }
      .zoom { display: inline-flex; align-items: center; gap: 6px; color: var(--secondary-text-color); flex: 1 1 200px; max-width: 320px; }
      .zoom input { flex: 1; min-width: 0; accent-color: var(--primary-color); }
      .zoom-val { font-size: var(--vr-font-sm); font-variant-numeric: tabular-nums; min-width: 2.5em; text-align: right; }
      /* RoomMind-like: smooth line, faint bands, event strip at the bottom, pill legend. */
      .chart-scroll { position: relative; }
      .plot-wrap { position: relative; }
      .plot-wrap .chart { width: 100%; touch-action: pan-x; }
      .chart .grid { stroke: var(--divider-color, rgba(128, 128, 128, 0.25)); stroke-width: 1; }
      .chart .axis { font-size: 11px; fill: var(--secondary-text-color); }
      .chart .sun { fill: rgba(128, 128, 128, 0.12); }
      .chart .sched { fill: var(--primary-color); opacity: 0.35; }
      .chart .target-band { fill: var(--success-color, #4caf50); opacity: 0.1; }
      .chart .target { stroke: var(--success-color, #4caf50); stroke-width: 2; stroke-dasharray: 6 4; }
      .chart .lux { fill: none; stroke: var(--primary-text-color); stroke-width: 2; stroke-linejoin: round; }
      .chart .light { fill: var(--warning-color, #ff8100); opacity: 0.55; cursor: pointer; outline: none; }
      .chart .light:hover, .chart .light:focus-visible, .chart .light.picked { opacity: 0.9; }
      .chart .now { stroke: rgba(128, 128, 128, 0.6); stroke-width: 1; stroke-dasharray: 4 4; }
      .chart .cross { stroke: rgba(128, 128, 128, 0.6); stroke-width: 1; }
      .tip { position: absolute; top: 18px; transform: translateX(10px); min-width: 140px; padding: 8px 10px; border-radius: 8px;
        background: var(--card-background-color, #fff); color: var(--primary-text-color); box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        font-size: 12px; line-height: 1.5; pointer-events: none; z-index: 2; white-space: nowrap; }
      .tip.flip { transform: translateX(calc(-100% - 10px)); }
      .tip-time { font-weight: 500; margin-bottom: 4px; }
      .tip-row { display: flex; align-items: center; gap: 6px; }
      .tip-row.sub { opacity: 0.75; }
      .tip-sep { border-top: 1px solid rgba(128, 128, 128, 0.3); margin-top: 4px; padding-top: 4px; }
      .legend { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin-top: var(--vr-space-2); }
      .lg { font: inherit; font-size: 12px; display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 12px;
        border: none; background: transparent; color: var(--primary-text-color); cursor: pointer; }
      .lg:hover { background: var(--vr-fill); }
      .lg.off { opacity: 0.35; }
      .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; flex: none; }
      .dot.lux { background: var(--primary-text-color); }
      .dot.target { background: var(--success-color, #4caf50); }
      .dot.light { background: var(--warning-color, #ff8100); }
      .dot.sched { background: var(--primary-color); opacity: 0.6; }
      .dot.sun { background: rgba(128, 128, 128, 0.45); }
      .picked { margin-top: var(--vr-space-2); padding: var(--vr-space-2) var(--vr-space-3); border: 1px solid var(--vr-border); border-radius: var(--vr-radius-sm); background: var(--vr-surface); font-size: var(--vr-font-sm); line-height: 1.5; }
    `]}};q([z({attribute:!1})],Y.prototype,`hass`,void 0),q([z({attribute:!1})],Y.prototype,`room`,void 0),q([z({attribute:!1})],Y.prototype,`sunEntity`,void 0),q([B()],Y.prototype,`_period`,void 0),q([B()],Y.prototype,`_historyDays`,void 0),q([B()],Y.prototype,`_data`,void 0),q([B()],Y.prototype,`_loading`,void 0),q([B()],Y.prototype,`_error`,void 0),q([B()],Y.prototype,`_picked`,void 0),q([B()],Y.prototype,`_debug`,void 0),q([B()],Y.prototype,`_tall`,void 0),q([B()],Y.prototype,`_hoverT`,void 0),q([B()],Y.prototype,`_hidden`,void 0),q([B()],Y.prototype,`_zoom`,void 0),q([B()],Y.prototype,`_viewH`,void 0),q([B()],Y.prototype,`_boxW`,void 0),Y=on=q([ke(`vr-room-analysis`)],Y);var X,Z={low:33,medium:67,high:100},ln=[`music_assistant`,`mass`];function un(e){return e.normalize(`NFKD`).replace(/[\u0300-\u036f]/g,``).toLowerCase().replace(/[^a-z0-9]+/g,`_`).replace(/^_+|_+$/g,``)}function dn(e){return e.time??(e.start?.type===`time`&&e.start.time?e.start.time:`22:00`)}var Q=class extends R{static{X=this}constructor(...e){super(...e),this.allRooms=[],this.enabledPersons=[],this.settings={persons:[],group_by_floor:!1},this._draft=null,this._saveState=`idle`,this._brightness=255,this._loadedDraft=null,this._tab=`settings`,this._addingLight=!1,this._selectedLights=new Set,this._addingMotion=!1,this._addingLinks=!1,this._selectedLinks=new Set,this._selectedMotion=new Set,this._addingLux=!1,this._selectedLux=new Set,this._addingSchedule=!1,this._debugOpen=!1,this._debugEntries=[],this._debugNow=null,this._closedSections=new Set,this._fullSections=new Set,this._openInfos=new Set,this._editingFans=!1,this._addingFans=!1,this._fanSelection=new Set,this._addingFanShare=!1,this._fanShareSelection=new Set,this._openCovers=new Set,this._coverTest=null,this._addingLocks=!1,this._lockSelection=new Set,this._openLocks=new Set,this._confirmLock=null,this._addingCovers=!1,this._coverSelection=new Set,this._addingMedia=!1,this._mediaSelection=new Set,this._addingVacuum=!1,this._vacuumSelection=new Set,this._openPlans=new Set,this._vacuumBusy=!1,this._vacuumError=``,this._addingDoor=!1,this._doorSelection=new Set,this._bundleAdd=null,this._bundleSel=new Set,this._converting=!1,this._convertError=``,this._openSlots=new Set,this._openBundles=new Set,this._groupEdit=null,this._groupSelection=new Set,this._groupNameDraft=``,this._openClocks=new Set,this._clockFolds=new Set,this._pickingAlarm=!1}connectedCallback(){super.connectedCallback(),this.room&&this._loadDraft()}updated(e){let t=!!this._draft&&(ht(this.hass,this._draft.area_id)!==null||gt(this.hass,this._draft.area_id)!==null);t&&this._graceTick===void 0?this._graceTick=window.setInterval(()=>this.requestUpdate(),1e3):!t&&this._graceTick!==void 0&&(window.clearInterval(this._graceTick),this._graceTick=void 0),e.has(`room`)&&this.room&&(this._draft&&this._draft.area_id===this.room.area_id||this._loadDraft()),e.has(`_draft`)&&this._draft&&this._draft!==this._loadedDraft&&this._scheduleSave()}disconnectedCallback(){super.disconnectedCallback(),window.clearInterval(this._graceTick),this._graceTick=void 0,window.clearInterval(this._debugTimer),this._debugTimer=void 0,this._debugOpen=!1,this._flushSave()}_loadDraft(){this._closedSections=new Set,this._fullSections=new Set,this._debugEntries=[],this._debugOpen&&this._loadDebug(),this._openInfos=new Set,this._draft=Nt(structuredClone(this.room),V(`bundles.default_name`,this.hass.language)),this._draft.linked_rooms=Ze([...this.allRooms.filter(e=>e.area_id!==this.room.area_id),this.room],this.room.area_id),(this._draft.cover_groups??[]).length>0&&(this._draft.covers_follow=this._draft.covers_follow??(this._draft.cover_groups??[]).some(e=>e.follow),this._draft.cover_groups=[]),this._draft.fan_shared_rooms=Ze([...this.allRooms.filter(e=>e.area_id!==this.room.area_id),this.room],this.room.area_id,`fan_shared_rooms`),this._loadedDraft=this._draft,window.clearTimeout(this._saveTimer),this._saveTimer=void 0,this._saveState=`idle`}_scheduleSave(){window.clearTimeout(this._saveTimer),this._saveState=`pending`,this._saveTimer=window.setTimeout(()=>{this._saveTimer=void 0,this._save()},500)}async _flushSave(){this._saveTimer!==void 0&&(window.clearTimeout(this._saveTimer),this._saveTimer=void 0,await this._save())}static{this.styles=[Me,o`
      :host {
        display: block;
        padding: var(--vr-space-4);
        max-width: 680px;
        margin: 0 auto;
      }

      /* Explanation texts: hidden unless the section's ⓘ is on. */
      .section:not(.show-info) .info-text,
      .section:not(.show-info) .dusk-hint {
        display: none;
      }

      .title-group {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        min-width: 0;
      }

      .info-btn {
        display: inline-grid;
        place-items: center;
        width: 28px;
        height: 28px;
        padding: 0;
        border: none;
        border-radius: 50%;
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
      }

      .info-btn ha-icon {
        --mdc-icon-size: 18px;
      }

      .info-btn:hover,
      .info-btn.active {
        color: var(--primary-color);
      }

      .section-info p {
        margin: 0;
      }

      .code-table {
        border-collapse: collapse;
        margin-top: var(--vr-space-1);
        width: 100%;
      }

      .code-table td {
        padding: 3px var(--vr-space-2) 3px 0;
        vertical-align: top;
        border-top: 1px solid var(--vr-border);
      }

      .code-table td:first-child {
        white-space: nowrap;
      }

      .section-info {
        margin: 0 0 var(--vr-space-3);
        padding: var(--vr-space-2) var(--vr-space-3);
        border-left: 3px solid var(--primary-color);
        background: var(--vr-fill-primary);
        font-size: var(--vr-font-sm);
        line-height: 1.5;
        color: var(--primary-text-color);
      }

      .debug-panel {
        margin: 0 0 var(--vr-space-4);
        padding: var(--vr-space-3);
        border: 1px dashed var(--vr-border-strong);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
      }

      .debug-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: var(--vr-space-2);
        flex-wrap: wrap;
      }

      .debug-title {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-weight: 500;
      }

      .debug-title ha-icon {
        --mdc-icon-size: 18px;
      }

      .debug-sub {
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
      }

      .debug-now {
        margin-top: var(--vr-space-2);
        padding: var(--vr-space-2);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-fill);
        font-size: var(--vr-font-xs);
      }

      .debug-now-title {
        font-weight: 500;
        margin-bottom: 4px;
      }

      .debug-now-grid {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 2px var(--vr-space-3);
      }

      .debug-now-k {
        color: var(--secondary-text-color);
      }

      .debug-now-bundle {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px;
        padding: 3px 0;
        border-top: 1px solid var(--vr-border);
      }

      .debug-pill {
        padding: 0 6px;
        border-radius: 999px;
        background: var(--vr-surface);
        color: var(--secondary-text-color);
      }

      .debug-pill.on {
        background: color-mix(in srgb, var(--vr-on) 25%, transparent);
        color: var(--primary-text-color);
      }

      .debug-flags {
        color: var(--secondary-text-color);
      }

      .debug-list {
        margin-top: var(--vr-space-2);
        max-height: 320px;
        overflow-y: auto;
        display: grid;
        gap: 2px;
      }

      .debug-row {
        display: grid;
        grid-template-columns: auto auto auto 1fr;
        align-items: start;
        gap: 6px;
        padding: 4px 6px;
        border-radius: 4px;
        font-size: var(--vr-font-xs);
        line-height: 1.4;
      }

      .debug-row:nth-child(odd) {
        background: var(--vr-fill);
      }

      .debug-row ha-icon {
        --mdc-icon-size: 16px;
        color: var(--secondary-text-color);
      }

      .debug-row.on ha-icon { color: var(--vr-on); }
      .debug-row.off ha-icon { color: var(--secondary-text-color); }
      .debug-row.blocked ha-icon, .debug-row.ignored ha-icon { color: var(--error-color); }
      .debug-row.adjust ha-icon { color: var(--primary-color); }

      .debug-time {
        font-variant-numeric: tabular-nums;
        color: var(--secondary-text-color);
      }

      .debug-kind {
        font-weight: 500;
        white-space: nowrap;
      }

      .debug-text {
        min-width: 0;
        overflow-wrap: anywhere;
      }

      .back-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        margin: 0 calc(-1 * var(--vr-space-1)) var(--vr-space-5);
        padding: var(--vr-space-1);
        position: sticky;
        top: 0;
        z-index: 2;
        background: var(--lovelace-background, var(--primary-background-color));
      }

      ha-icon-button {
        --mdc-icon-button-size: 40px;
        --mdc-icon-size: 20px;
        color: var(--primary-text-color);
      }

      h1 {
        font-size: var(--vr-font-xl);
        font-weight: 500;
        color: var(--primary-text-color);
        margin: 0;
      }

      /* ── master controls ───────────────────── */
      .master-card {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius);
        padding: var(--vr-space-4);
        margin-bottom: var(--vr-space-5);
        display: flex;
        flex-direction: column;
        gap: var(--vr-space-3);
      }

      .master-row {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--vr-space-2) var(--vr-space-3);
      }

      .master-label {
        font-size: var(--vr-font-md);
        color: var(--secondary-text-color);
        flex: 1 0 auto;
      }

      .on-badge {
        font-size: var(--vr-font-sm);
        font-weight: 500;
        padding: 2px 10px;
        border-radius: 20px;
        background: var(--vr-on-bg);
        color: var(--vr-on);
      }

      .off-badge {
        font-size: var(--vr-font-sm);
        font-weight: 500;
        padding: 2px 10px;
        border-radius: 20px;
        background: var(--vr-fill);
        color: var(--secondary-text-color);
      }

      .brightness-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
      }

      .brightness-row ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
        flex: none;
      }

      input[type="range"] {
        flex: 1;
        min-width: 0;
        accent-color: var(--primary-color);
      }

      .brightness-pct {
        font-size: var(--vr-font-sm);
        font-weight: 500;
        color: var(--primary-text-color);
        min-width: 36px;
        text-align: right;
      }

      /* ── sections ──────────────────────────── */
      .section {
        margin-bottom: var(--vr-space-5);
      }

      .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: var(--vr-space-3);
      }

      .section-title {
        font-size: var(--vr-font-sm);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--secondary-text-color);
      }

      .add-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: var(--vr-font-sm);
        color: var(--primary-color);
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px 6px;
        border-radius: var(--vr-radius-sm);
      }

      .add-btn:hover {
        background: var(--vr-fill-primary);
      }

      /* ── light rows ────────────────────────── */
      .light-list {
        display: flex;
        flex-direction: column;
        gap: var(--vr-space-2);
      }

      .light-list .light-row.pinned + .fixed-row {
        margin-top: calc(-1 * var(--vr-space-2));
      }

      .light-row {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        padding: var(--vr-space-3) var(--vr-space-4);
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
      }

      .light-row ha-icon {
        --mdc-icon-size: 20px;
        flex: none;
      }

      .cover-row {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
      }

      .cover-row.open {
        border-color: var(--primary-color);
      }

      .cover-row-head {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        padding: var(--vr-space-2) var(--vr-space-2) var(--vr-space-2) var(--vr-space-4);
      }

      .cover-row-head > ha-icon {
        --mdc-icon-size: 20px;
        flex: none;
      }

      .cover-row-btn {
        flex: 1;
        min-width: 0;
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        font: inherit;
        color: inherit;
        background: none;
        border: none;
        padding: 0;
        text-align: left;
        cursor: pointer;
        min-height: var(--vr-touch, 44px);
      }

      .cover-row-btn .light-entity {
        flex: 1;
      }

      .cover-row-btn ha-icon {
        --mdc-icon-size: 20px;
        color: var(--secondary-text-color);
        flex: none;
      }

      .cover-chip {
        font-size: var(--vr-font-xs);
        padding: 1px 6px;
        border-radius: var(--vr-radius-sm);
        background: var(--vr-fill-primary);
        color: var(--primary-color);
        white-space: nowrap;
      }

      .cover-row-body {
        border-top: 1px solid var(--vr-border);
        padding: var(--vr-space-1) var(--vr-space-4) var(--vr-space-3);
      }

      .cover-ask {
        margin-top: var(--vr-space-2);
        padding: var(--vr-space-3);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-fill-primary);
      }

      .cover-ask-btns {
        display: flex;
        flex-wrap: wrap;
        gap: var(--vr-space-2);
        margin-top: var(--vr-space-2);
      }

      .light-entity {
        flex: 1;
        font-size: var(--vr-font-md);
        color: var(--primary-text-color);
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .light-state {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .light-state.on {
        color: var(--vr-on);
        font-weight: 500;
      }

      .light-state.active {
        color: var(--vr-motion);
        font-weight: 500;
      }

      .remove-btn {
        --mdc-icon-button-size: 36px;
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
      }

      .empty-hint {
        font-size: var(--vr-font-md);
        color: var(--secondary-text-color);
        padding: var(--vr-space-3) 0;
      }

      /* ── multi-select light chooser ─────────── */
      .chooser {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      .chooser-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        min-height: var(--vr-touch);
        padding: 0 var(--vr-space-1);
        border-radius: var(--vr-radius-sm);
        cursor: pointer;
        font-size: var(--vr-font-md);
        color: var(--primary-text-color);
      }

      .chooser-row:hover {
        background: var(--vr-fill);
      }

      .chooser-row input {
        width: 18px;
        height: 18px;
        margin: 0;
        accent-color: var(--primary-color);
        flex: none;
      }

      .manual-card {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius);
        padding: var(--vr-space-3) var(--vr-space-4);
        margin-bottom: var(--vr-space-5);
      }

      .manual-card.active {
        border: 1px dashed var(--primary-color);
        background: var(--vr-fill-primary);
      }

      .manual-head {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
      }

      .manual-head > ha-icon {
        --mdc-icon-size: 22px;
        color: var(--primary-color);
        flex: none;
      }

      .manual-text {
        flex: 1;
        min-width: 0;
      }

      .manual-title {
        font-size: var(--vr-font-md);
        font-weight: 500;
        color: var(--primary-text-color);
      }

      .manual-sub {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }

      .light-row.pinned {
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
      }

      .pin-btn {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        font: inherit;
        font-size: var(--vr-font-sm);
        font-weight: 500;
        min-height: 32px;
        min-width: 32px;
        padding: 0 8px;
        border-radius: 16px;
        border: 1px solid transparent;
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
        font-variant-numeric: tabular-nums;
      }

      .pin-btn ha-icon {
        --mdc-icon-size: 18px;
      }

      .pin-btn:hover {
        background: var(--vr-fill);
      }

      .pin-btn.active {
        color: var(--primary-color);
        border-color: var(--primary-color);
        background: var(--vr-fill-primary);
      }

      .fixed-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        margin-top: -1px;
        padding: var(--vr-space-2) var(--vr-space-4);
        background: var(--vr-fill-primary);
        border: 1px solid var(--vr-border);
        border-top: none;
        border-radius: 0 0 var(--vr-radius-sm) var(--vr-radius-sm);
      }

      .fixed-label {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        white-space: nowrap;
      }

      .fixed-row input[type="range"] {
        flex: 1;
        accent-color: var(--primary-color);
      }

      .fixed-num {
        font-size: var(--vr-font-sm);
        font-weight: 500;
        min-width: 40px;
        text-align: right;
        font-variant-numeric: tabular-nums;
        color: var(--primary-text-color);
      }

      .group-list {
        display: flex;
        flex-direction: column;
        gap: var(--vr-space-2);
      }

      .group-card {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        padding: var(--vr-space-3) var(--vr-space-4);
      }

      .group-card.on {
        border-color: color-mix(in srgb, var(--vr-on) 40%, var(--vr-border));
      }

      .group-card.editing {
        border-color: var(--primary-color);
      }

      .group-card.editing .picker-card {
        border: none;
        padding: 0;
        margin-top: var(--vr-space-2) !important;
      }

      .group-head {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
      }

      .group-head > ha-icon {
        --mdc-icon-size: 22px;
        flex: none;
      }

      .group-name {
        flex: 1;
        min-width: 0;
        font: inherit;
        font-size: var(--vr-font-md);
        font-weight: 500;
        color: var(--primary-text-color);
        background: none;
        border: 1px solid transparent;
        border-radius: var(--vr-radius-sm);
        padding: 6px 8px;
      }

      .group-card.editing > .group-name {
        width: 100%;
        box-sizing: border-box;
        border-color: var(--vr-border);
      }

      .group-name:hover,
      .group-name:focus {
        border-color: var(--vr-border);
        outline: none;
      }

      .group-name:focus-visible {
        border-color: var(--primary-color);
      }

      .group-lamps {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: var(--vr-space-2);
      }

      .lamp-chip {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        font-size: var(--vr-font-sm);
        padding: 3px 10px;
        border-radius: 12px;
        background: var(--vr-fill);
        color: var(--secondary-text-color);
      }

      .lamp-chip.on {
        background: var(--vr-on-bg);
        color: var(--primary-text-color);
      }

      .lamp-chip ha-icon {
        --mdc-icon-size: 12px;
        color: var(--primary-color);
      }

      .group-actions {
        display: flex;
        justify-content: flex-end;
        gap: var(--vr-space-2);
        margin-top: var(--vr-space-2);
      }

      .fan-step {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--vr-space-2) var(--vr-space-3);
        padding: var(--vr-space-2) 0;
        border-bottom: 1px solid var(--vr-border);
      }

      .fan-field {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .fan-field input[type="number"] {
        width: 56px;
        font: inherit;
        font-size: var(--vr-font-md);
        padding: 4px 6px;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        color: var(--primary-text-color);
      }

      .fan-speed {
        flex: 1 1 140px;
        min-width: 0;
      }

      .fan-speed input[type="range"] {
        flex: 1;
        min-width: 0;
        width: 100%;
        accent-color: var(--primary-color);
      }

      .fan-arrow {
        color: var(--secondary-text-color);
      }

      .cover-buttons {
        display: flex;
        gap: var(--vr-space-2);
        margin-top: var(--vr-space-3);
      }

      .cover-buttons .chooser-btn {
        flex: 1;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        min-height: 36px;
      }

      .cover-buttons ha-icon {
        --mdc-icon-size: 16px;
      }

      .cover-follow {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        margin-top: var(--vr-space-3);
        padding-top: var(--vr-space-3);
        border-top: 1px solid var(--vr-border);
      }

      .chooser-btn.danger {
        color: var(--error-color);
      }

      .segmented {
        display: inline-flex;
        flex: none;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        overflow: hidden;
      }

      .segmented button {
        font: inherit;
        font-size: var(--vr-font-sm);
        padding: 6px 10px;
        min-height: 32px;
        border: none;
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
      }

      .segmented button + button {
        border-left: 1px solid var(--vr-border);
      }

      .segmented button.active {
        background: var(--vr-fill-primary);
        color: var(--primary-color);
        font-weight: 500;
      }

      .ha-name {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--vr-space-2);
      }

      .ha-name ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
      }

      .ha-name .group-name {
        border-color: var(--vr-border);
        min-width: 140px;
      }

      .bundle-title {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-weight: 500;
      }

      .bundle-expand {
        flex: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        padding: 0;
        border: none;
        border-radius: 50%;
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
      }

      .bundle-expand:hover {
        background: var(--vr-fill-primary);
        color: var(--primary-color);
      }

      .swatch {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 1px solid var(--vr-border-strong);
        vertical-align: -2px;
        margin-left: 4px;
      }

      .schedule-key {
        font-family: ui-monospace, monospace;
        font-size: var(--vr-font-xs);
        background: var(--vr-fill);
        border-radius: 4px;
        padding: 1px 5px;
      }

      .motion-note {
        margin: var(--vr-space-2) 0 0;
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .motion-note.warn {
        color: var(--primary-text-color);
        background: color-mix(in srgb, var(--warning-color, #f59e0b) 14%, transparent);
        border-radius: var(--vr-radius-sm);
        padding: var(--vr-space-2) var(--vr-space-3);
      }

      .motion-status {
        display: flex;
        flex-wrap: wrap;
        gap: var(--vr-space-2);
      }

      .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: var(--vr-font-sm);
        padding: 4px 10px;
        border-radius: 14px;
        background: var(--vr-fill);
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }

      .status-chip ha-icon {
        --mdc-icon-size: 16px;
      }

      .status-chip.on {
        background: color-mix(in srgb, var(--vr-motion) 12%, transparent);
        color: var(--vr-motion);
        font-weight: 500;
      }

      .status-chip.grace {
        background: color-mix(in srgb, var(--vr-motion) 8%, transparent);
        border: 1px dashed color-mix(in srgb, var(--vr-motion) 60%, transparent);
        color: var(--primary-text-color);
      }

      .chooser-caption {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        padding: 0 var(--vr-space-1) var(--vr-space-1);
      }

      .chooser-row.disabled {
        cursor: default;
        opacity: 0.55;
      }

      .chooser-row.disabled:hover {
        background: none;
      }

      .chooser-all {
        border-bottom: 1px solid var(--vr-border);
        border-radius: 0;
        color: var(--secondary-text-color);
        font-size: var(--vr-font-sm);
      }

      .chooser-name {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .chooser-actions {
        display: flex;
        justify-content: flex-end;
        gap: var(--vr-space-2);
        margin-top: var(--vr-space-2);
      }

      .chooser-btn {
        font-size: var(--vr-font-sm);
        font-weight: 500;
        padding: 6px 14px;
        border-radius: var(--vr-radius-sm);
        border: 1px solid var(--vr-border);
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
      }

      .chooser-btn.primary {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }

      .chooser-btn:disabled {
        opacity: 0.4;
        cursor: default;
      }

      /* ── entity picker card ────────────────── */
      .picker-card {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        padding: var(--vr-space-3) var(--vr-space-4);
      }

      ha-entity-picker {
        display: block;
        width: 100%;
      }

      /* ── lux section ──────────────────────── */
      .lux-status {
        display: flex;
        align-items: center;
        gap: var(--vr-space-4);
        margin-top: var(--vr-space-3);
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .lux-val {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
      }

      .lux-num {
        font-size: 20px;
        font-weight: 500;
        color: var(--primary-text-color);
        font-variant-numeric: tabular-nums;
      }

      .lux-label {
        font-size: var(--vr-font-xs);
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      .lux-sep {
        font-size: var(--vr-font-xl);
        color: var(--vr-border-strong);
      }

      .lux-adapt-btn {
        margin-left: auto;
        font-size: var(--vr-font-sm);
        color: var(--primary-color);
        background: var(--vr-fill-primary);
        border: none;
        border-radius: var(--vr-radius-sm);
        padding: 6px 12px;
        cursor: pointer;
      }

      .lux-adapt-btn:hover {
        background: color-mix(in srgb, var(--primary-color) 18%, transparent);
      }

      .target-lux-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        margin-top: var(--vr-space-3);
      }

      .target-lux-row ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
        flex: none;
      }

      .target-lux-row input[type="range"] {
        flex: 1;
        min-width: 0;
        accent-color: var(--primary-color);
      }

      .slider-num {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        flex: none;
        font-size: var(--vr-font-sm);
        color: var(--primary-text-color);
      }

      .slider-num input {
        font: inherit;
        font-weight: 500;
        font-variant-numeric: tabular-nums;
        width: 4.5em;
        min-height: 32px;
        padding: 4px 6px;
        text-align: right;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        color: var(--primary-text-color);
        box-sizing: border-box;
      }

      .slider-num input:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: 1px;
      }

      .slider-unit {
        color: var(--secondary-text-color);
        min-width: 1.6em;
      }

      .slider-extra {
        color: var(--secondary-text-color);
        font-size: var(--vr-font-xs);
        white-space: nowrap;
      }

      .target-lux-num {
        font-size: var(--vr-font-sm);
        font-weight: 500;
        color: var(--primary-text-color);
        min-width: 52px;
        text-align: right;
      }

      /* ── dusk toggle row ───────────────────── */
      .dusk-row {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        padding: var(--vr-space-3) var(--vr-space-4);
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
      }

      .dusk-icon {
        --mdc-icon-size: 20px;
        color: var(--vr-dusk);
        flex: none;
      }

      .dusk-text {
        flex: 1;
      }

      .dusk-title {
        font-size: var(--vr-font-md);
        color: var(--primary-text-color);
      }

      .dusk-hint {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        margin-top: 2px;
      }

      .dim-btn {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font: inherit;
        font-size: var(--vr-font-sm);
        font-weight: 500;
        min-height: 32px;
        padding: 0 12px;
        border-radius: 16px;
        border: 1px solid var(--vr-border);
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
      }

      .dim-btn ha-icon {
        --mdc-icon-size: 16px;
      }

      .dim-btn.active {
        background: var(--vr-fill-primary);
        border-color: var(--primary-color);
        color: var(--primary-color);
      }

      .alarm-card {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        padding: var(--vr-space-3) var(--vr-space-4);
      }

      .alarm-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--vr-space-2);
        flex-wrap: wrap;
      }

      .alarm-question {
        font-size: var(--vr-font-md);
        font-weight: 500;
        color: var(--primary-text-color);
      }

      .alarm-pill {
        font-size: var(--vr-font-xs);
        padding: 2px 10px;
        border-radius: 999px;
        background: var(--vr-fill);
        color: var(--secondary-text-color);
        white-space: nowrap;
      }

      .alarm-pill.armed {
        background: color-mix(in srgb, var(--warning-color, #f59e0b) 18%, transparent);
        color: var(--primary-text-color);
      }

      .alarm-panel {
        margin: 2px 0 var(--vr-space-3);
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .link-btn {
        font: inherit;
        background: none;
        border: none;
        padding: 0 0 0 4px;
        color: var(--primary-color);
        cursor: pointer;
      }

      .alarm-options {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: var(--vr-space-2);
      }

      .alarm-opt {
        font: inherit;
        text-align: left;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
        padding: var(--vr-space-2) var(--vr-space-3);
        min-height: var(--vr-touch, 44px);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        color: var(--primary-text-color);
        cursor: pointer;
      }

      .alarm-opt:hover {
        border-color: var(--vr-border-strong);
      }

      .alarm-opt.selected {
        border-color: var(--primary-color);
        box-shadow: inset 0 0 0 1px var(--primary-color);
        background: var(--vr-fill-primary);
      }

      .alarm-opt ha-icon {
        --mdc-icon-size: 20px;
        color: var(--secondary-text-color);
      }

      .alarm-opt.selected ha-icon {
        color: var(--primary-color);
      }

      .alarm-opt-title {
        font-size: var(--vr-font-sm);
        font-weight: 500;
      }

      .alarm-opt-hint {
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
        line-height: 1.4;
      }

      .alarm-tabs {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: var(--vr-space-1);
        padding: 4px;
        border-radius: var(--vr-radius-sm);
        background: var(--vr-fill);
      }

      .alarm-tab {
        font: inherit;
        font-size: var(--vr-font-sm);
        font-weight: 500;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        min-height: var(--vr-touch, 44px);
        padding: 6px 4px;
        border: none;
        border-radius: var(--vr-radius-sm);
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
        text-align: center;
      }

      .alarm-tab.selected {
        background: var(--vr-surface);
        color: var(--primary-text-color);
        box-shadow: 0 0 0 1px var(--vr-border);
      }

      .alarm-tab-now {
        font-weight: 400;
        color: var(--primary-color);
      }

      .alarm-tab-sub {
        font-size: var(--vr-font-xs);
        font-weight: 400;
        color: var(--secondary-text-color);
      }

      .alarm-sub {
        margin: var(--vr-space-3) 0 var(--vr-space-2);
        padding-top: var(--vr-space-3);
        border-top: 1px solid var(--vr-border);
        font-size: var(--vr-font-md);
        font-weight: 500;
        color: var(--primary-text-color);
      }

      .alarm-pill.running {
        background: color-mix(in srgb, var(--vr-motion) 18%, transparent);
        color: var(--primary-text-color);
      }

      .fan-sub {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--vr-space-2);
      }

      .fan-sub .link-btn {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: var(--vr-font-sm);
        font-weight: 400;
      }

      .fan-steps {
        display: grid;
        gap: var(--vr-space-1);
      }

      .fan-step-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        padding: 4px 4px 4px var(--vr-space-2);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
      }

      .fan-step-row input[type="range"] {
        flex: 1;
        min-width: 0;
      }

      .fan-speed-seg {
        flex: 1 1 auto;
        display: inline-grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .fan-speed-seg button {
        min-height: 32px;
        padding: 6px 8px;
      }

      .target-lux-row .fan-speed-seg {
        flex: 1;
      }

      .fan-step-time {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        flex: none;
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .fan-step-time input {
        font: inherit;
        width: 3.2em;
        min-height: 32px;
        padding: 4px 6px;
        text-align: right;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        color: var(--primary-text-color);
        box-sizing: border-box;
      }

      .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: var(--vr-space-2);
      }

      .chip {
        font: inherit;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        min-height: 32px;
        padding: 2px 6px 2px 10px;
        border: 1px solid var(--vr-border);
        border-radius: 999px;
        background: var(--vr-surface);
        font-size: var(--vr-font-sm);
        color: var(--primary-text-color);
      }

      .chip ha-icon {
        --mdc-icon-size: 16px;
        color: var(--secondary-text-color);
      }

      .chip-add {
        padding-right: 12px;
        color: var(--primary-color);
        cursor: pointer;
      }

      .chip-add ha-icon {
        color: var(--primary-color);
      }

      .chip-x {
        display: inline-grid;
        place-items: center;
        width: 24px;
        height: 24px;
        padding: 0;
        border: none;
        border-radius: 50%;
        background: none;
        cursor: pointer;
      }

      .chip-x:hover {
        background: var(--vr-fill);
      }

      .fold-btn {
        font: inherit;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        min-height: 32px;
        padding: 0;
        border: none;
        background: none;
        cursor: pointer;
        color: inherit;
      }

      .fold-btn ha-icon {
        --mdc-icon-size: 20px;
        color: var(--secondary-text-color);
      }

      .fold-summary ha-icon {
        --mdc-icon-size: 18px;
        flex: none;
        margin-left: auto;
      }

      .fold-summary-text {
        flex: 1;
        min-width: 0;
      }

      .item-cards {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: var(--vr-space-2);
      }

      .item-card {
        font: inherit;
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        width: 100%;
        min-width: 0;
        text-align: left;
        padding: var(--vr-space-2) var(--vr-space-3);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        color: var(--primary-text-color);
        cursor: pointer;
      }

      .item-icon {
        --mdc-icon-size: 22px;
        flex: none;
        color: var(--secondary-text-color);
      }

      .item-icon.ok {
        color: var(--success-color, #43a047);
      }

      .item-icon.warn {
        color: var(--warning-color, #ffa600);
      }

      .item-icon.on {
        color: var(--vr-on);
      }

      .item-text {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .item-title {
        font-weight: 500;
        font-size: var(--vr-font-sm);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .item-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }

      .item-pill {
        font-size: var(--vr-font-xs);
        padding: 1px 8px;
        border: 1px solid var(--vr-border);
        border-radius: 999px;
        color: var(--secondary-text-color);
      }

      .item-status {
        flex: none;
        font-size: var(--vr-font-xs);
        padding: 2px 10px;
        border-radius: 999px;
        background: var(--vr-fill);
        color: var(--secondary-text-color);
        white-space: nowrap;
      }

      .item-status.ok {
        background: color-mix(in srgb, var(--success-color, #43a047) 15%, transparent);
        color: var(--success-color, #43a047);
      }

      .item-status.warn {
        background: color-mix(in srgb, var(--warning-color, #ffa600) 18%, transparent);
        color: var(--primary-text-color);
      }

      .item-status.on {
        background: color-mix(in srgb, var(--vr-on) 22%, transparent);
        color: var(--primary-text-color);
      }

      .item-chev {
        --mdc-icon-size: 18px;
        flex: none;
        color: var(--secondary-text-color);
      }

      .fold-summary {
        font: inherit;
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        width: 100%;
        text-align: left;
        padding: var(--vr-space-2) var(--vr-space-3);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        line-height: 1.5;
        cursor: pointer;
      }

      .fold-summary:hover {
        border-color: var(--vr-border-strong);
      }

      .lux-modes {
        grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
      }

      .lux-alarm {
        margin-top: var(--vr-space-3);
      }

      .lux-alarm .chip-row {
        margin-top: var(--vr-space-1);
      }

      .chip-toggle {
        padding-right: 12px;
        cursor: pointer;
      }

      .chip-toggle.on {
        border-color: var(--primary-color);
        background: var(--vr-fill-primary);
      }

      .chip-toggle.on ha-icon {
        color: var(--primary-color);
      }

      .bundle-card {
        min-width: 0;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
      }

      .bundle-card.open {
        border-color: var(--primary-color);
        box-shadow: inset 0 0 0 1px var(--primary-color);
      }

      .bundle-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        padding: var(--vr-space-2) var(--vr-space-3);
        min-height: var(--vr-touch, 44px);
        cursor: pointer;
      }

      .bundle-row.open {
        cursor: default;
        border-bottom: 1px solid var(--vr-border);
      }

      .bundle-icon {
        --mdc-icon-size: 22px;
        flex: none;
        color: var(--secondary-text-color);
      }

      .bundle-icon.on {
        color: var(--vr-on);
      }

      .bundle-text {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      .bundle-sub {
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .bundle-move {
        display: inline-flex;
        flex-direction: column;
        flex: none;
      }

      .move-btn {
        display: grid;
        place-items: center;
        width: 24px;
        height: 18px;
        padding: 0;
        border: none;
        border-radius: 4px;
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
      }

      .move-btn ha-icon {
        --mdc-icon-size: 18px;
      }

      .move-btn:hover:not([disabled]) {
        background: var(--vr-fill);
        color: var(--primary-color);
      }

      .move-btn[disabled] {
        opacity: 0.3;
        cursor: default;
      }

      .bundle-body {
        padding: var(--vr-space-3);
      }

      .alarm-pill.lit {
        background: color-mix(in srgb, var(--vr-on) 22%, transparent);
        color: var(--primary-text-color);
      }

      .alarm-opt[disabled],
      .chip[disabled] {
        opacity: 0.55;
        cursor: not-allowed;
      }

      .danger-link {
        color: var(--error-color);
        padding-left: 8px;
      }

      .alarm-fixed {
        display: grid;
        gap: var(--vr-space-2);
      }

      .alarm-fixed-row {
        display: flex;
        align-items: flex-start;
        gap: var(--vr-space-3);
        padding: var(--vr-space-2) var(--vr-space-3);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
      }

      .alarm-fixed-row ha-icon {
        --mdc-icon-size: 20px;
        color: var(--secondary-text-color);
        flex: none;
        margin-top: 2px;
      }

      .alarm-fixed-row.now {
        border-color: var(--primary-color);
        background: var(--vr-fill-primary);
      }

      .alarm-fixed-row.now ha-icon {
        color: var(--primary-color);
      }

      .alarm-fixed-row > div {
        flex: 1;
        min-width: 0;
      }

      .alarm-home-modes {
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        margin-top: var(--vr-space-2);
      }

      .alarm-opt-head {
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
      }

      .alarm-fixed-row .alarm-opt ha-icon {
        margin-top: 0;
      }

      .alarm-fixed-row .alarm-opt:not(.selected) ha-icon {
        color: var(--secondary-text-color);
      }

      .clock-time {
        font-size: 22px;
        font-weight: 500;
        font-variant-numeric: tabular-nums;
        color: var(--primary-text-color);
        flex: none;
      }

      .clock-time.off {
        color: var(--secondary-text-color);
      }

      .clock-line {
        display: flex;
        flex-wrap: wrap;
        gap: var(--vr-space-3);
        align-items: flex-end;
      }

      .clock-field {
        display: inline-flex;
        flex-direction: column;
        gap: 4px;
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
      }

      .clock-input {
        font: inherit;
        font-size: var(--vr-font-md);
        min-height: 36px;
        padding: 4px 8px;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        color: var(--primary-text-color);
        box-sizing: border-box;
      }

      .chip-day {
        min-width: 40px;
        justify-content: center;
        padding: 2px 10px;
        cursor: pointer;
      }

      .chip-day.on {
        border-color: var(--primary-color);
        background: var(--vr-fill-primary);
        color: var(--primary-color);
        font-weight: 500;
      }

      .clock-steps {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
        gap: 6px;
        margin-top: var(--vr-space-2);
      }

      .clock-step {
        display: grid;
        gap: 2px;
        padding: 6px 8px;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        text-align: center;
      }

      .clock-step-at {
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
      }

      .clock-step-pct {
        font-size: var(--vr-font-md);
        font-weight: 500;
      }

      .clock-step-bar {
        height: 4px;
        border-radius: 2px;
        background: var(--vr-fill);
        overflow: hidden;
      }

      .clock-step-bar span {
        display: block;
        height: 100%;
        background: var(--vr-on);
      }

      .vacuum-done {
        --mdc-icon-size: 20px;
        color: var(--disabled-text-color, var(--secondary-text-color));
        flex: none;
      }

      .vacuum-done.today {
        color: var(--success-color, #43a047);
      }

      .vacuum-sub {
        display: block;
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
        font-weight: 400;
      }

      .convert-card {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        margin-top: var(--vr-space-2);
        padding: var(--vr-space-3);
        border: 1px solid var(--primary-color);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-fill-primary);
      }

      .convert-card > ha-icon {
        --mdc-icon-size: 22px;
        color: var(--primary-color);
        flex: none;
      }

      .slot-list {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: var(--vr-space-2);
      }

      .slot-row {
        min-width: 0;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        padding: var(--vr-space-2) var(--vr-space-3);
      }

      .slot-head {
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        margin-bottom: var(--vr-space-2);
      }

      .slot-name {
        flex: 1 1 auto;
        width: 0;
        min-width: 0;
        box-sizing: border-box;
        font-weight: 500;
      }

      .slot-folded {
        font: inherit;
        width: 100%;
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        text-align: left;
        background: var(--vr-surface);
        color: var(--primary-text-color);
        cursor: pointer;
      }

      .slot-folded-wrap {
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
      }

      .slot-folded-wrap .slot-folded {
        flex: 1;
        min-width: 0;
        border: none;
        padding: 0;
        background: transparent;
      }

      .slot-off .slot-folded-name,
      .slot-off .slot-name {
        color: var(--secondary-text-color);
      }

      .slot-folded ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
        flex: none;
      }

      .slot-folded-text {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
      }

      .slot-folded-name {
        font-size: var(--vr-font-sm);
        font-weight: 500;
      }

      .slot-folded-sub {
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .slot-days-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
      }

      /* Days side by side on one line (compact chips), Dim level small at the far right. */
      .slot-days-row .slot-days {
        flex: 1;
        min-width: 0;
        flex-wrap: nowrap;
        gap: 4px;
      }

      .slot-days-row .chip-day {
        min-width: 0;
        flex: 0 1 34px;
        padding: 2px 4px;
        font-size: var(--vr-font-xs);
      }

      /* Start, end, normal/vacation and remove on one line: compact fields. */
      .slot-times {
        display: flex;
        flex-wrap: wrap;
        row-gap: var(--vr-space-2);
        align-items: center;
        gap: 6px;
        margin-top: var(--vr-space-2);
        min-width: 0;
      }

      .slot-times .clock-input {
        font-size: var(--vr-font-sm);
        min-height: 30px;
        padding: 2px 4px;
        min-width: 0;
        flex: 0 1 auto;
      }

      .slot-times select.clock-input {
        max-width: 110px;
      }

      .slot-times input[type="time"].clock-input {
        width: 84px;
      }

      .slot-dim-row ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
        flex: none;
      }

      .slot-times .remove-btn {
        flex: none;
        --mdc-icon-button-size: 32px;
      }

      .slot-until {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .lock-icon.locked {
        color: var(--success-color, #43a047);
      }
      .lock-icon.unlocked {
        color: var(--warning-color, #f59e0b);
      }
      .lock-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 4px;
      }
      .lock-state {
        flex: none;
        font-size: var(--vr-font-xs);
        padding: 2px 10px;
        border-radius: 999px;
        background: var(--vr-fill);
        color: var(--secondary-text-color);
        white-space: nowrap;
      }
      .lock-state.locked {
        background: color-mix(in srgb, var(--success-color, #43a047) 14%, transparent);
        color: var(--success-color, #43a047);
      }
      .lock-state.unlocked {
        background: color-mix(in srgb, var(--warning-color, #f59e0b) 14%, transparent);
        color: var(--warning-color, #f59e0b);
      }
      .lock-btn {
        flex: none;
      }
      .lock-confirm {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: var(--vr-space-2);
        margin: 0 var(--vr-space-3) var(--vr-space-3);
        padding: var(--vr-space-2) var(--vr-space-3);
        border: 1px solid color-mix(in srgb, var(--warning-color, #f59e0b) 50%, transparent);
        border-radius: var(--vr-radius-sm);
        background: color-mix(in srgb, var(--warning-color, #f59e0b) 10%, transparent);
        font-size: var(--vr-font-sm);
      }
      .lock-confirm ha-icon {
        --mdc-icon-size: 18px;
        color: var(--warning-color, #f59e0b);
        margin-right: 6px;
        vertical-align: -3px;
      }
      .lock-confirm-acts {
        display: flex;
        gap: var(--vr-space-2);
      }
      .chooser-btn.danger {
        color: var(--error-color, #db4437);
        border-color: color-mix(in srgb, var(--error-color, #db4437) 50%, transparent);
      }
      .clock-fold {
        margin-top: var(--vr-space-3);
        padding-top: var(--vr-space-2);
        border-top: 1px solid var(--vr-border);
      }
      .clock-fold-head {
        font: inherit;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px 8px;
        width: 100%;
        padding: 4px 0;
        border: 0;
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
        text-align: left;
      }
      .clock-fold-title {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-right: 4px;
        font-size: var(--vr-font-md);
        font-weight: 500;
      }
      .clock-fold-title ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
      }
      .clock-fold-body {
        padding-top: var(--vr-space-2);
      }
      .clock-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        height: 22px;
        padding: 0 9px 0 7px;
        border: 1px solid var(--vr-border);
        border-radius: 999px;
        background: var(--vr-fill);
        font-size: var(--vr-font-sm);
        line-height: 1;
        white-space: nowrap;
        color: var(--primary-text-color);
      }
      .clock-pill ha-icon {
        --mdc-icon-size: 14px;
        color: var(--secondary-text-color);
      }
      .clock-pill.light ha-icon {
        color: var(--vr-on);
      }
      .clock-pill.vol ha-icon,
      .clock-pill.cover ha-icon {
        color: var(--primary-color);
      }
      .clock-pill.stop {
        border-color: color-mix(in srgb, var(--error-color, #db4437) 40%, transparent);
        background: color-mix(in srgb, var(--error-color, #db4437) 10%, transparent);
        color: var(--error-color, #db4437);
      }
      .clock-pill.stop ha-icon {
        color: var(--error-color, #db4437);
      }
      .clock-pill.off {
        border-style: dashed;
        background: transparent;
        color: var(--secondary-text-color);
      }
      .clock-steps-row {
        overflow-x: auto;
      }
      .clock-step-bar.vol span {
        background: var(--primary-color);
      }
      .clock-legend-dot.vol {
        background: var(--primary-color);
      }
      .clock-stop-btn {
        font: inherit;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 2px;
        padding: 0;
        border: 0;
        background: none;
        cursor: pointer;
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
        white-space: nowrap;
      }
      .clock-stop-btn ha-icon {
        --mdc-icon-size: 14px;
      }
      .clock-check {
        font: inherit;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 0;
        border: 0;
        background: none;
        cursor: pointer;
        font-size: var(--vr-font-xs);
        color: var(--primary-text-color);
      }
      .clock-check ha-icon {
        --mdc-icon-size: 14px;
        color: var(--secondary-text-color);
      }
      .clock-check.on ha-icon {
        color: var(--primary-color);
      }
      .clock-warn {
        color: var(--warning-color, #f59e0b);
      }
      .clock-step-bar.cover {
        margin-top: 3px;
      }

      .clock-step-bar.cover span {
        background: var(--primary-color);
      }

      .clock-legend {
        display: flex;
        gap: var(--vr-space-3);
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
        margin-top: var(--vr-space-1);
      }

      .clock-legend-dot {
        display: inline-block;
        width: 10px;
        height: 4px;
        border-radius: 2px;
        background: var(--vr-on);
        vertical-align: middle;
        margin-right: 4px;
      }

      .clock-legend-dot.cover {
        background: var(--primary-color);
      }

      .clock-steps-label {
        display: flex;
        align-items: center;
        gap: var(--vr-space-1);
        font-size: var(--vr-font-sm);
        font-weight: 500;
        margin-top: var(--vr-space-3);
      }

      .clock-steps-label ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
      }

      .alarm-summary {
        margin-top: var(--vr-space-3);
        padding: var(--vr-space-2) var(--vr-space-3);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-fill);
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        line-height: 1.5;
      }

      .required-hint {
        display: flex;
        align-items: center;
        gap: 6px;
        margin: var(--vr-space-2) 0 0;
        font-size: var(--vr-font-sm);
        font-weight: 500;
        color: var(--error-color);
      }

      .required-hint ha-icon {
        --mdc-icon-size: 16px;
      }

      /* ── tabs ──────────────────────────────── */
      .tabs {
        display: flex;
        gap: var(--vr-space-1);
        border-bottom: 1px solid var(--vr-border);
        margin-bottom: var(--vr-space-5);
      }

      .tabs button {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font: inherit;
        font-size: var(--vr-font-md);
        padding: var(--vr-space-2) var(--vr-space-3);
        min-height: var(--vr-touch);
        background: none;
        border: none;
        border-bottom: 2px solid transparent;
        margin-bottom: -1px;
        color: var(--secondary-text-color);
        cursor: pointer;
      }

      .tabs button ha-icon {
        --mdc-icon-size: 18px;
      }

      .tabs button[aria-selected="true"] {
        color: var(--primary-color);
        border-bottom-color: var(--primary-color);
        font-weight: 500;
      }

      /* ── save status (top bar) ──────────────── */
      .save-status {
        margin-left: auto;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        white-space: nowrap;
      }

      .save-status ha-icon {
        --mdc-icon-size: 16px;
      }

      .save-status.saved {
        color: var(--success-color, #43a047);
      }

      .save-status.error {
        color: var(--error-color);
      }

      .retry-link {
        background: none;
        border: none;
        padding: 0 0 0 4px;
        color: var(--primary-color);
        font: inherit;
        text-decoration: underline;
        cursor: pointer;
      }

      .spin {
        animation: vr-spin 1s linear infinite;
      }

      @keyframes vr-spin {
        to {
          transform: rotate(360deg);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .spin {
          animation: none;
        }
      }
    `]}render(){let e=this._draft;if(!e)return L;let t=this.hass.language,n=ut(this.hass,e,this.enabledPersons),r=e.lights.length;return dt(n.avg_brightness),F`
      <div class="back-row">
        <ha-icon-button
          .label=${V(`room.back`,t)}
          .path=${`M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z`}
          @click=${this._back}
        ></ha-icon-button>
        <h1>${e.name}</h1>
        <button class="info-btn debug-btn ${this._debugOpen?`active`:``}"
          aria-pressed=${this._debugOpen?`true`:`false`}
          aria-label=${V(`debug.title`,t)} title=${V(`debug.title`,t)}
          @click=${this._toggleDebug}>
          <ha-icon icon=${this._debugOpen?`mdi:bug`:`mdi:bug-outline`}></ha-icon>
        </button>
        <span class="save-status ${this._saveState}" role="status" aria-live="polite">
          ${this._saveState===`pending`||this._saveState===`saving`?F`<ha-icon icon="mdi:loading" class="spin"></ha-icon>${V(`room.saving`,t)}`:this._saveState===`saved`?F`<ha-icon icon="mdi:check"></ha-icon>${V(`room.saved`,t)}`:this._saveState===`error`?F`<ha-icon icon="mdi:alert-circle-outline"></ha-icon>${V(`room.error_save`,t)}
                <button class="retry-link" @click=${this._save}>${V(`common.retry`,t)}</button>`:L}
        </span>
      </div>

      ${this._debugOpen?this._renderDebug():L}

      <!-- Master controls -->
      <div class="master-card">
        <div class="master-row">
          <ha-icon icon="mdi:lightbulb-group" style="--mdc-icon-size:22px; color: ${n.any_on?`var(--vr-on)`:`var(--secondary-text-color)`}"></ha-icon>
          <span class="master-label">
            ${(e.groups??[]).length>0?`${(e.groups??[]).length} ${(e.groups??[]).length===1?V(`card.bundle`,t):V(`card.bundles`,t)}`:`${r} ${V(r===1?`card.lights`:`card.lights_plural`,t)}`}
          </span>
          ${n.any_on?F`<span class="on-badge">${V(`card.on`,t)}</span>`:F`<span class="off-badge">${V(`card.off`,t)}</span>`}
          ${e.lights.length>0&&gt(this.hass,e.area_id)===null?F`
            <button
              class="dim-btn"
              title=${V(`manual.hint`,t)}
              @click=${()=>this._toggleManual(!1)}
            >
              <ha-icon icon="mdi:hand-back-right-outline"></ha-icon>${V(`manual.start`,t)}
            </button>
          `:L}
          ${e.lights.length>0?F`
            <button
              class="dim-btn ${mt(this.hass,e.area_id)?`active`:``}"
              aria-pressed=${mt(this.hass,e.area_id)}
              title=${mt(this.hass,e.area_id)?V(`dim.restore`,t):V(`dim.to_1`,t)}
              @click=${this._toggleDim}
            >
              <ha-icon icon="mdi:brightness-4"></ha-icon>${V(`dim.button`,this.hass.language)}
            </button>
          `:L}
          <vr-toggle
            .checked=${n.any_on}
            .disabled=${!n.any_on&&!n.allowed}
            @change=${e=>this._masterToggle(e.detail.value)}
          ></vr-toggle>
        </div>

        ${n.any_on?F`
          <div class="brightness-row">
            <ha-icon icon="mdi:brightness-4"></ha-icon>
            <input
              type="range"
              min="1"
              max="255"
              step="1"
              .value=${String(n.avg_brightness??255)}
              @change=${this._onBrightnessChange}
            />
            ${this._num(n.avg_brightness===null?100:Math.round((n.avg_brightness??255)/255*100),1,100,`%`,V(`groups.brightness`,t),e=>this._setRoomBrightness(Math.round(e*255/100)))}
          </div>
          ${Object.keys(e.fixed_levels??{}).length>0?F`<div class="master-row" style="font-size: var(--vr-font-sm); color: var(--secondary-text-color);">
                <ha-icon icon="mdi:pin" style="--mdc-icon-size:16px"></ha-icon>
                ${V(`fixed.slider_hint`,t)}:
                ${e.lights.filter(t=>e.fixed_levels?.[t.entity_id]!==void 0).map(t=>`${this.hass.states[t.entity_id]?.attributes.friendly_name??t.entity_id} ${e.fixed_levels[t.entity_id]}%`).join(`, `)}
              </div>`:L}
        `:L}

        ${n.motion_detected?F`
          <div class="master-row" style="font-size: var(--vr-font-sm); color: var(--vr-motion);">
            <ha-icon icon="mdi:motion-sensor" style="--mdc-icon-size:16px; color: var(--vr-motion)"></ha-icon>
            ${V(`card.motion`,t)}
          </div>
        `:L}
        ${this._renderGraceRow(e)}
        ${this._renderFanStatus(e)}

      </div>

      ${e.lights.length>0&&gt(this.hass,e.area_id)!==null?this._renderManual(e):L}

      ${e.lights.length>0||(e.covers??[]).length>0?F`
        <div class="picker-card full-control ${e.full_control?`active`:``}" style="margin-top: var(--vr-space-2)">
          <div class="cover-follow" style="margin-top: 0; padding-top: 0; border-top: none">
            <ha-icon icon=${e.full_control?`mdi:shield-lock`:`mdi:shield-lock-open-outline`}
              style="--mdc-icon-size:20px; flex: none; color: ${e.full_control?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
            <div class="dusk-text">
              <div class="dusk-title">${V(`full_control.title`,t)}</div>
              <div class="dusk-hint">${V(e.full_control?`full_control.on_hint`:`full_control.off_hint`,t)}</div>
            </div>
            <vr-toggle
              .checked=${!!e.full_control}
              @change=${e=>this._patch({full_control:e.detail.value})}
            ></vr-toggle>
          </div>
        </div>
      `:L}

      <!-- Tabs -->
      <div class="tabs" role="tablist">
        <button
          role="tab"
          aria-selected=${this._tab===`settings`}
          @click=${()=>{this._tab=`settings`}}
        >
          <ha-icon icon="mdi:cog-outline"></ha-icon>${V(`room.tab_settings`,t)}
        </button>
        <button
          role="tab"
          aria-selected=${this._tab===`analysis`}
          @click=${()=>{this._tab=`analysis`}}
        >
          <ha-icon icon="mdi:chart-bar"></ha-icon>${V(`room.tab_analysis`,t)}
        </button>
      </div>

      ${this._tab===`analysis`?F`<vr-room-analysis role="tabpanel" .hass=${this.hass} .room=${e} .sunEntity=${this.settings.sun_entity||e.sun_entity||`sun.sun`}></vr-room-analysis>`:F`
      <!-- Lamps: bundles -->
      ${this._renderBundles(e)}

      <!-- Linked rooms section -->
      <div class="section ${this._infoOpen(`links`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`links`,V(`room.links_section`,t))}
          ${this._shown(`links`)?F`<button class="add-btn" @click=${()=>{this._setFull(`links`,!0),this._selectedLinks=new Set,this._addingLinks=!0}}>
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>
            ${V(`room.links_add`,t)}
          </button>`:L}
        </div>
        ${this._infoText(`links`)}
        ${this._isOpen(`links`)?F`
        ${(e.linked_rooms??[]).length===0?this._addingLinks?L:F`<p class="empty-hint">${V(`room.links_none`,t)}</p>`:F`<div class="light-list">
              ${(e.linked_rooms??[]).map(e=>F`
                <div class="light-row">
                  <ha-icon icon="mdi:link-variant" style="color: var(--secondary-text-color)"></ha-icon>
                  <span class="light-entity">${this._areaName(e)}</span>
                  <ha-icon-button
                    class="remove-btn"
                    .label=${V(`common.remove`,t)}
                    .path=${`M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z`}
                    @click=${()=>this._removeLink(e)}
                  ></ha-icon-button>
                </div>
              `)}
            </div>`}
        ${this._addingLinks?this._renderMultiChooser({available:Je(this.hass,this.allRooms).map(e=>e.area_id).filter(t=>t!==e.area_id&&!(e.linked_rooms??[]).includes(t)),selected:()=>this._selectedLinks,icon:()=>`mdi:link-variant`,name:e=>this._areaName(e),emptyText:V(`room.links_none_available`,t),onChange:e=>{this._selectedLinks=e},onCancel:()=>{this._addingLinks=!1},onConfirm:e=>this._addLinks(e)}):L}
        ${(()=>{let n=e.linked_rooms??[];if(n.length===0)return L;let r=Qe([...this.allRooms.filter(t=>t.area_id!==e.area_id).map(t=>n.includes(t.area_id)&&!(t.linked_rooms??[]).includes(e.area_id)?{...t,linked_rooms:[...t.linked_rooms??[],e.area_id]}:t),e],e.area_id).filter(t=>t!==e.area_id);return F`<p class="empty-hint" style="padding-bottom: 0">
            <span class="info-text">${V(`room.links_hint`,t)}</span>
            ${r.length>n.length?F`<br />${V(`room.links_group`,t)}: ${r.map(e=>this._areaName(e)).join(`, `)}`:L}
          </p>`})()}
        `:this._foldItems(`links`,(e.linked_rooms??[]).map(e=>{let n=G(this.hass,e)?.state===`on`;return{icon:`mdi:link-variant`,title:this._areaName(e),pills:[V(`fold.link_motion`,t)],status:V(n?`card.on`:`card.off`,t),tone:n?`on`:``}}),V(`room.links_none`,t))}
      </div>

      <!-- Presence section -->
      <div class="section ${this._infoOpen(`presence`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`presence`,V(`room.presence_section`,t))}
        </div>
        ${this._infoText(`presence`)}
        ${this._isOpen(`presence`)?F`
        ${this.enabledPersons.length===0?F`<p class="empty-hint">${V(`room.presence_no_persons`,t)}</p>`:F`
            <div class="picker-card chooser">
              ${this.enabledPersons.map(n=>{let r=this.hass.states[n],i=r?.state===`home`,a=r?.attributes.friendly_name??n;return F`
                  <label class="chooser-row" title=${n}>
                    <input
                      type="checkbox"
                      .checked=${(e.persons??[]).includes(n)}
                      @change=${()=>this._togglePerson(n)}
                    />
                    <vr-person-avatar .hass=${this.hass} .entityId=${n} .size=${28}></vr-person-avatar>
                    <span class="chooser-name">${a}</span>
                    <span class="light-state">${V(i?`person.home`:`person.away`,t)}</span>
                  </label>
                `})}
            </div>
            <p class="empty-hint info-text" style="padding-bottom: 0">${V(`room.presence_hint`,t)}</p>
          `}
        ${(this.settings.late_home_persons??[]).length>0?F`
          <div class="cover-follow">
            <ha-icon icon="mdi:home-clock-outline" style="--mdc-icon-size:20px; flex: none; color: ${e.late_home?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
            <div class="dusk-text">
              <div class="dusk-title">${V(`room.late_home`,t)}</div>
              <div class="alarm-opt-hint">${V(e.late_home?`room.late_home_on`:`room.late_home_off`,t)}${this._lateHomeNow()?F`<br /><strong>${V(`room.late_home_active`,t).replace(`{names}`,this._lateHomeNow())}</strong>`:L}</div>
            </div>
            <vr-toggle .checked=${!!e.late_home} @change=${e=>this._patch({late_home:e.detail.value})}></vr-toggle>
          </div>`:L}
        `:this._foldItems(`presence`,(e.persons??[]).filter(e=>this.enabledPersons.includes(e)).map(e=>{let n=this.hass.states[e]?.state===`home`;return{icon:n?`mdi:account`:`mdi:account-outline`,title:this._entName(e),status:V(n?`fold.home`:`fold.away`,t),tone:n?`ok`:``}}),this.enabledPersons.length===0?V(`fold.presence_none_enabled`,t):V(`fold.presence_none`,t))}
      </div>

      ${W(e).length===0&&U(this.hass,e.area_id,`binary_sensor`,[`motion`,`occupancy`,`presence`]).length===0?L:F`
      <!-- Motion sensors section (one or more; any on = motion) -->
      <div class="section ${this._infoOpen(`motion`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`motion`,V(`room.motion_section`,t))}
          ${this._shown(`motion`)?F`<button class="add-btn" @click=${()=>{this._setFull(`motion`,!0),this._selectedMotion=new Set,this._addingMotion=!0}}>
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>
            ${V(`room.sensor_add`,t)}
          </button>`:L}
        </div>
        ${this._infoText(`motion`)}
        ${this._isOpen(`motion`)?F`

        ${W(e).length===0?this._addingMotion?L:F`<p class="empty-hint">${V(`room.motion_none`,t)}</p>`:F`<div class="light-list">
              ${W(e).map((n,r)=>{let i=this.hass.states[n]?.state,a=i===`on`||i===`detected`;return F`${this._renderSensorRow(n,a?`mdi:motion-sensor`:`mdi:motion-sensor-off`,a?`var(--vr-motion)`:`var(--secondary-text-color)`,V(a?`card.motion`:`room.motion_clear`,t),a,()=>this._removeMotion(n),this._mover(W(e),r,e=>this._patch({motion_sensors:e,motion_sensor:``})))}${this._renderMotionWindow(e,n)}`})}
            </div>
            <p class="empty-hint info-text" style="padding-bottom: 0">${V(`motion_window.hint`,t)}</p>`}

        ${this._addingMotion?this._renderMultiChooser({available:U(this.hass,e.area_id,`binary_sensor`,[`motion`,`occupancy`,`presence`]).filter(t=>!W(e).includes(t)),selected:()=>this._selectedMotion,icon:()=>`mdi:motion-sensor`,emptyText:V(`room.area_no_motion`,t),onChange:e=>{this._selectedMotion=e},onCancel:()=>{this._addingMotion=!1},onConfirm:e=>this._addMotion(e)}):L}
        ${W(e).length>0?F`
          <div class="picker-card" style="margin-top: var(--vr-space-2)">
            <div class="motion-status">
              <span class="status-chip ${n.motion_detected?`on`:``}">
                <ha-icon icon=${n.motion_detected?`mdi:motion-sensor`:`mdi:motion-sensor-off`}></ha-icon>
                ${n.motion_detected?V(`card.motion`,t):V(`room.motion_clear`,t)}
              </span>
              ${(()=>{let n=ht(this.hass,e.area_id);return n===null?L:F`<span class="status-chip grace">
                      <ha-icon icon="mdi:timer-sand"></ha-icon>
                      ${V(`grace.label`,t)} · ${V(`grace.left`,t)} ${K(n)}
                    </span>`})()}
            </div>
            ${this._renderMotionDiagnostics(e)}
            <div class="target-lux-row">
              <ha-icon icon="mdi:timer-outline"></ha-icon>
              <input
                type="range"
                min="0"
                max="600"
                step="30"
                aria-label=${V(`grace.setting`,t)}
                .value=${String(e.motion_off_delay??300)}
                @input=${this._onGraceInput}
              />
              ${this._num(e.motion_off_delay??300,0,3600,`s`,V(`grace.setting`,t),e=>this._patch({motion_off_delay:e}),F`<span class="slider-extra">${K(e.motion_off_delay??300)}</span>`)}
            </div>
            <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">
              ${V(`grace.setting`,t)}: ${(e.motion_off_delay??300)===0?V(`grace.immediately`,t):`${K(e.motion_off_delay??300)} min`}.
              <span class="info-text">${V(`grace.setting_hint`,t)}</span>
            </p>
          </div>
        `:L}
        ${W(e).length>1?F`<p class="empty-hint info-text" style="padding-bottom: 0">${V(`room.motion_multi_hint`,t)}</p>`:L}
        `:this._foldItems(`motion`,W(e).map(e=>{let n=this.hass.states[e],r=n?.state===`on`||n?.state===`detected`,i=this._battery(e);return{icon:r?`mdi:motion-sensor`:`mdi:motion-sensor-off`,title:this._entName(e),pills:[n?.last_changed?`${V(`fold.last`,t)} ${this._when(n.last_changed)}`:``,i?`${V(`fold.battery`,t)} ${i.text}`:``].filter(Boolean),status:!n||n.state===`unavailable`?V(`fold.unavailable`,t):V(r?`card.motion`:`room.motion_clear`,t),tone:i?.low||!n||n.state===`unavailable`?`warn`:r?`on`:``}}),V(`room.motion_none`,t))}
      </div>
      `}

      <!-- Curtains section -->
      ${this._renderCovers(e)}

      <!-- Media player section -->
      ${this._renderMedia(e)}

      <!-- Vacuum section -->
      ${this._renderVacuum(e)}

      <!-- Fan section -->
      ${this._renderFans(e)}

      <!-- Door sensors section -->
      ${this._renderDoors(e)}

      <!-- Locks section -->
      ${this._renderLocks(e)}

      ${this._renderDoorbell(e)}

      <!-- Alarm section -->
      ${this._renderClocks(e)}

      ${this._renderAlarm(e)}

      ${this._renderSmart(e)}

      ${at(e).length===0&&U(this.hass,e.area_id,`sensor`,[`illuminance`]).length===0?L:F`
      <!-- Lux sensors section (one or more, combined with lux_mode) -->
      ${this._renderLux(e,n.current_lux)}
      `}
      `}
    `}_renderAreaPicker(e,t,n,r,i=``){return e.length===0?F`<div class="picker-card" style=${i}>
        <p class="empty-hint" style="padding: 0">${n}</p>
      </div>`:F`
      <div class="picker-card" style=${i}>
        <ha-entity-picker
          .hass=${this.hass}
          .includeEntities=${e}
          .label=${t}
          @value-changed=${r}
        ></ha-entity-picker>
      </div>
    `}static _moved(e,t,n){let r=t+n;if(t<0||r<0||r>=e.length)return e;let i=[...e];return[i[t],i[r]]=[i[r],i[t]],i}_moveCtl(e){if(!e||e.count<2)return L;let t=this.hass.language;return F`<span class="bundle-move" @click=${e=>e.stopPropagation()}>
      <button class="move-btn" ?disabled=${e.index===0}
        aria-label="${V(`bundles.move_up`,t)}: ${e.name}" title=${V(`bundles.move_up`,t)}
        @click=${()=>e.onMove(-1)}>
        <ha-icon icon="mdi:chevron-up"></ha-icon></button>
      <button class="move-btn" ?disabled=${e.index===e.count-1}
        aria-label="${V(`bundles.move_down`,t)}: ${e.name}" title=${V(`bundles.move_down`,t)}
        @click=${()=>e.onMove(1)}>
        <ha-icon icon="mdi:chevron-down"></ha-icon></button>
    </span>`}_mover(e,t,n){let r=e[t],i=this.hass.states[r]?.attributes.friendly_name??r;return{index:t,count:e.length,name:i,onMove:r=>n(X._moved(e,t,r))}}_renderSensorRow(e,t,n,r,i,a,o){return F`
      <div class="light-row">
        <ha-icon icon=${t} style="color: ${n}"></ha-icon>
        <span class="light-entity" title=${e}>${this.hass.states[e]?.attributes.friendly_name??e}</span>
        <span class="light-state ${i?`active`:``}">${r}</span>
        ${this._moveCtl(o)}
        <ha-icon-button
          class="remove-btn"
          .label=${V(`common.remove`,this.hass.language)}
          .path=${`M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z`}
          @click=${a}
        ></ha-icon-button>
      </div>
    `}async _back(){await this._flushSave(),this.dispatchEvent(new CustomEvent(`back`,{bubbles:!0,composed:!0}))}async _masterToggle(e){let t=this.room.lights.map(e=>e.entity_id);await this._flushSave(),await Ue(this.hass,this.room.area_id,t,e)}async _onBrightnessChange(e){await this._setRoomBrightness(Number(e.target.value))}async _setRoomBrightness(e){this._brightness=e,await He(this.hass,We(this._draft??this.room),e)}_num(e,t,n,r,i,a,o=L,s=1){let c=s<1?String(s).split(`.`)[1]?.length??1:0,l=r=>{let i=Number(r.value.replace(`,`,`.`));if(r.value.trim()===``||!Number.isFinite(i)){r.value=String(e);return}let o=Number(Math.min(n,Math.max(t,Math.round(i/s)*s)).toFixed(c));r.value=String(o),o!==e&&a(o)};return F`<span class="slider-num">
      <input
        type="number"
        inputmode=${s<1?`decimal`:`numeric`}
        min=${t}
        max=${n}
        step=${s}
        aria-label=${i}
        .value=${String(e)}
        @change=${e=>l(e.target)}
        @keydown=${e=>{e.key===`Enter`&&e.target.blur()}}
      />
      <span class="slider-unit">${r}</span>
      ${o}
    </span>`}_addLight(){this._selectedLights=new Set,this._addingLight=!0}_availableLights(e){return U(this.hass,e.area_id,`light`).filter(t=>!e.lights.some(e=>e.entity_id===t))}_renderLightChooser(e){return this._renderMultiChooser({available:this._availableLights(e),selected:()=>this._selectedLights,icon:e=>this.hass.states[e]?.state===`on`?`mdi:lightbulb`:`mdi:lightbulb-outline`,emptyText:V(`room.area_no_lights`,this.hass.language),onChange:e=>{this._selectedLights=e},onCancel:()=>this._cancelAddLights(),onConfirm:()=>this._confirmAddLights()})}_renderMultiChooser(e){let t=this.hass.language;if(e.available.length===0)return F`<div class="picker-card" style="margin-top: var(--vr-space-2)">
        <p class="empty-hint" style="padding: 0">${e.emptyText}</p>
        <div class="chooser-actions">
          <button class="chooser-btn" @click=${e.onCancel}>${V(`common.close`,t)}</button>
        </div>
      </div>`;let n=e.selected(),r=e.available.every(e=>n.has(e)),i=t=>{let n=new Set(e.selected());n.has(t)?n.delete(t):n.add(t),e.onChange(n)};return F`
      <div class="picker-card chooser" style="margin-top: var(--vr-space-2)">
        ${e.available.length>1?F`
          <label class="chooser-row chooser-all">
            <input
              type="checkbox"
              .checked=${r}
              @change=${()=>e.onChange(e.available.every(t=>e.selected().has(t))?new Set:new Set(e.available))}
            />
            <span>${V(`room.lights_select_all`,t)}</span>
          </label>
        `:L}
        ${e.available.map(t=>{let r=this.hass.states[t],a=r?.state===`on`||r?.state===`detected`,o=e.name?e.name(t):r?.attributes.friendly_name??t;return F`
            <label class="chooser-row" title=${t}>
              <input type="checkbox" .checked=${n.has(t)} @change=${()=>i(t)} />
              <ha-icon
                icon=${e.icon(t)}
                style="--mdc-icon-size:18px; color: ${a?`var(--vr-on)`:`var(--secondary-text-color)`}"
              ></ha-icon>
              <span class="chooser-name">${o}</span>
            </label>
          `})}
        <div class="chooser-actions">
          <button class="chooser-btn" @click=${e.onCancel}>${V(`common.cancel`,t)}</button>
          <button
            class="chooser-btn primary"
            ?disabled=${n.size===0}
            @click=${()=>e.onConfirm(e.available.filter(t=>e.selected().has(t)))}
          >
            ${V(`room.lights_add_selected`,t)} (${n.size})
          </button>
        </div>
      </div>
    `}_cancelAddLights(){this._addingLight=!1,this._selectedLights=new Set}_confirmAddLights(){if(!this._draft)return;let e=new Set(this._draft.lights.map(e=>e.entity_id)),t=this._availableLights(this._draft).filter(t=>this._selectedLights.has(t)&&!e.has(t));this._draft={...this._draft,lights:[...this._draft.lights,...t.map(e=>({entity_id:e}))]},this._cancelAddLights()}_removeLight(e){if(!this._draft)return;let t=[...this._draft.lights],[n]=t.splice(e,1),r=this._draft.daylight_lights?.filter(e=>e!==n?.entity_id),i={...this._draft.fixed_levels??{}};n&&delete i[n.entity_id];let a={...this._draft,lights:t,daylight_lights:r,fixed_levels:i};this._draft=n?Dt(a,n.entity_id):a}_renderFans(e){let t=this.hass.language,n=e.fans??[],r=e.fan_shared_rooms??[],i=$e(this.allRooms,e,`fan_shared_rooms`).filter(t=>t!==e.area_id),a=[];for(let e of i)for(let t of this.allRooms.find(t=>t.area_id===e)?.fans??[])t&&!n.includes(t)&&!a.some(e=>e.id===t)&&a.push({id:t,room:e});let o=n.length+a.length,s=U(this.hass,e.area_id,`fan`);if(o===0&&r.length===0&&s.length===0)return L;let c=e.fan_steps??[],l=c.length>0?null:i.map(e=>this.allRooms.find(t=>t.area_id===e)).find(e=>(e?.fan_steps??[]).length>0)??null,u=G(this.hass,e.area_id),d=u?.attributes.activity_since,f=u?.attributes.fan_percentage,p=u?.attributes.fan_temp_active===!0,m=u?.attributes.fan_off_at,h=e=>this.hass.states[e]?.attributes.friendly_name??e,g=e=>{let n=this.hass.states[e];if(!n)return`—`;let r=n.attributes.percentage;return n.state===`on`?typeof r==`number`?`${r}%`:V(`card.on`,t):V(`card.off`,t)},_=[...n,...a.map(e=>e.id)].map(e=>this.hass.states[e]).find(e=>e?.state===`on`),v=_?.attributes.percentage,y=d&&typeof f==`number`?V(`fan.reason_activity`,t):p?V(`fan.reason_temp`,t):``,b=_?`${V(`alarm.now`,t)}: ${typeof v==`number`?`${v}%`:V(`card.on`,t)}${y?` · ${y}`:``}`:`${V(`alarm.now`,t)}: ${V(`card.off`,t)}`,x=e.fan_motion!==!1,S=e.fan_temp_sensor!==void 0,C=!x&&!S,ee=e=>this._patch({fan_motion:e?void 0:!1}),w=t=>{t?this._patch({fan_temp_sensor:e.fan_temp_sensor??this._temperatureSensors(e.area_id)[0]??``,fan_temp_min:e.fan_temp_min??24,fan_temp_speed:e.fan_temp_speed??Z.medium}):this._patch({fan_temp_sensor:void 0,fan_temp_min:void 0,fan_temp_speed:void 0})},T=[{id:`motion`,icon:`mdi:motion-sensor`,selected:x,click:()=>ee(!x)},{id:`temp`,icon:`mdi:thermometer`,selected:S,click:()=>w(!S)},{id:`manual`,icon:`mdi:hand-back-right-outline`,selected:C,click:()=>{C||this._patch({fan_motion:!1,fan_temp_sensor:void 0,fan_temp_min:void 0,fan_temp_speed:void 0})}}],te=K(e.motion_off_delay??300),E=typeof e.fan_run_on==`number`,D=(c.length?c:l?.fan_steps??[]).map(e=>e.percentage).filter(e=>e>0),O=[];x&&D.length&&O.push(V(`fan.sum_motion`,t).replace(`{from}`,this._fanLevelName(Math.min(...D))).replace(`{to}`,this._fanLevelName(Math.max(...D)))),S&&e.fan_temp_sensor&&O.push(V(`fan.sum_temp`,t).replace(`{lo}`,String(e.fan_temp_min??24)).replace(`{speed}`,this._fanLevelName(e.fan_temp_speed??Z.medium)));let k=O.length===0?V(`fan.sum_manual`,t):`${V(`fan.sum_prefix`,t)} ${O.join(V(`fan.sum_and`,t))}${O.length>1?V(`fan.sum_highest`,t):`.`}`+(x?` ${V(`fan.sum_run_on`,t).replace(`{time}`,K(E?e.fan_run_on:e.motion_off_delay??300))}`:``),A=this._isOpen(`fan`);return F`
      <div class="section ${this._infoOpen(`fan`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`fan`,V(`fan.section`,t))}
          ${A?F`<button class="add-btn" @click=${()=>{this._editingFans=!0,this._fanSelection=new Set,this._addingFans=!0}}>
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>${V(`fan.add`,t)}
          </button>`:o>0?F`<span class="alarm-pill ${_?`running`:``}">${b}</span>`:L}
        </div>
        ${this._infoText(`fan`)}
        ${A?F`
        <div class="alarm-card">
          <!-- which fan(s) -->
          <p class="alarm-panel" style="margin-top: 0">
            ${o===0?V(`fan.none`,t):[...n.map(e=>h(e)),...a.map(e=>`${h(e.id)} (${V(`fan.shared_via`,t).replace(`{room}`,this._areaName(e.room))})`)].join(`, `)}
            ${o>0?F`<button class="link-btn" @click=${()=>{this._editingFans=!this._editingFans,this._fanSelection=new Set,this._addingFans=!1}}>
              ${V(`fan.change`,t)}
            </button>`:L}
          </p>
          ${this._editingFans||o===0&&this._addingFans?F`
            <div class="light-list" style="margin-bottom: var(--vr-space-2)">
              ${n.map((e,t)=>this._renderSensorRow(e,this.hass.states[e]?.state===`on`?`mdi:fan`:`mdi:fan-off`,this.hass.states[e]?.state===`on`?`var(--vr-motion)`:`var(--secondary-text-color)`,g(e),this.hass.states[e]?.state===`on`,()=>this._patch({fans:n.filter(t=>t!==e)}),this._mover(n,t,e=>this._patch({fans:e}))))}
            </div>
            ${this._addingFans?this._renderMultiChooser({available:s.filter(e=>!n.includes(e)),selected:()=>this._fanSelection,icon:()=>`mdi:fan`,emptyText:V(`fan.none_in_area`,t),onChange:e=>{this._fanSelection=e},onCancel:()=>{this._addingFans=!1},onConfirm:e=>{this._patch({fans:[...n,...e]}),this._addingFans=!1}}):L}
            ${n.length>0?this._renderHaName(e,`fans_name`,V(`ha_name.fans_default`,t),`mdi:fan`):L}
          `:L}

          ${o>0?F`
            <div class="alarm-question" style="display: block; margin: var(--vr-space-3) 0 var(--vr-space-2)">${V(`fan.when`,t)}</div>
            <div class="alarm-options" role="group" aria-label=${V(`fan.when`,t)}>
              ${T.map(e=>F`
                <button
                  class="alarm-opt ${e.selected?`selected`:``}"
                  role=${e.id===`manual`?`radio`:`checkbox`}
                  aria-checked=${e.selected?`true`:`false`}
                  @click=${e.click}
                >
                  <ha-icon icon=${e.icon}></ha-icon>
                  <span class="alarm-opt-title">${V(`fan.trigger_${e.id}`,t)}</span>
                  <span class="alarm-opt-hint">${V(`fan.trigger_${e.id}_hint`,t)}</span>
                </button>
              `)}
            </div>

            ${x?F`
              <div class="alarm-sub fan-sub">
                <span>${V(`fan.steps_title`,t)}</span>
                <button class="link-btn" @click=${this._addFanStep}>
                  <ha-icon icon="mdi:plus" style="--mdc-icon-size:14px"></ha-icon>${V(`fan.add_step`,t)}
                </button>
              </div>
              ${W(e).length===0?F`<p class="required-hint" role="alert"><ha-icon icon="mdi:alert-circle-outline"></ha-icon>${V(`fan.needs_motion`,t)}</p>`:L}
              ${c.length===0?F`<p class="empty-hint" style="padding: 0">${l?V(`fan.steps_shared`,t).replace(`{room}`,this._areaName(l.area_id)).replace(`{steps}`,(l.fan_steps??[]).map(e=>`${e.minutes} min → ${e.percentage}%`).join(`, `)):V(`fan.steps_none`,t)}</p>`:F`<div class="fan-steps">
                    ${c.map((e,n)=>F`
                      <div class="fan-step-row">
                        <label class="fan-step-time">
                          <span>${V(`fan.after`,t)}</span>
                          <input
                            type="number" min="0" max="240" step="1" inputmode="numeric"
                            aria-label="${V(`fan.after`,t)} (${V(`fan.minutes`,t)})"
                            .value=${String(e.minutes)}
                            @change=${e=>this._setFanStep(n,{minutes:Number(e.target.value)})}
                          />
                          <span>${V(`fan.minutes`,t)}</span>
                        </label>
                        ${this._fanSpeedButtons(e.percentage,`${V(`fan.speed`,t)} ${V(`fan.after`,t).toLowerCase()} ${e.minutes} ${V(`fan.minutes`,t)}`,e=>this._setFanStep(n,{percentage:e}))}
                        <ha-icon-button
                          class="remove-btn"
                          .label=${V(`common.remove`,t)}
                          .path=${`M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z`}
                          @click=${()=>this._patch({fan_steps:c.filter((e,t)=>t!==n)})}
                        ></ha-icon-button>
                      </div>
                    `)}
                  </div>`}
              <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">
                ${d?F`${V(`fan.active_since`,t)} ${new Date(d).toLocaleTimeString(t,{hour:`2-digit`,minute:`2-digit`})}${typeof f==`number`?F` · ${V(`fan.speed`,t)} ${f}%`:L}`:V(`fan.idle`,t)}
              </p>
            `:L}

            ${S?F`
              <div class="alarm-sub">${V(`fan.trigger_temp`,t)}</div>
              ${this._renderFanTempFields(e)}
            `:L}

            ${x?F`
              <div class="alarm-sub">${V(`fan.run_on_how_long`,t)}</div>
              <div class="alarm-options" role="radiogroup" aria-label=${V(`fan.run_on_how_long`,t)}>
                <button class="alarm-opt ${E?``:`selected`}" role="radio" aria-checked=${E?`false`:`true`}
                  @click=${()=>this._patch({fan_run_on:void 0})}>
                  <ha-icon icon="mdi:timer-sand"></ha-icon>
                  <span class="alarm-opt-title">${V(`fan.run_on_grace`,t)}</span>
                  <span class="alarm-opt-hint">${te}</span>
                </button>
                <button class="alarm-opt ${E?`selected`:``}" role="radio" aria-checked=${E?`true`:`false`}
                  @click=${()=>{E||this._patch({fan_run_on:e.motion_off_delay??300})}}>
                  <ha-icon icon="mdi:fan-clock"></ha-icon>
                  <span class="alarm-opt-title">${V(`fan.run_on_own`,t)}</span>
                  <span class="alarm-opt-hint">${E?K(e.fan_run_on):V(`fan.run_on_own_hint`,t)}</span>
                </button>
              </div>
              ${E?F`
                <div class="target-lux-row">
                  <input type="range" min="0" max="1800" step="30" aria-label=${V(`fan.run_on_own`,t)}
                    .value=${String(Math.min(e.fan_run_on,1800))}
                    @input=${e=>this._patch({fan_run_on:Number(e.target.value)})} />
                  ${this._num(e.fan_run_on,0,3600,`s`,V(`fan.run_on_own`,t),e=>this._patch({fan_run_on:e}),F`<span class="slider-extra">${K(e.fan_run_on)}</span>`)}
                </div>`:L}
              ${m?F`<p class="empty-hint" style="padding: var(--vr-space-1) 0 0"><strong>${V(`fan.run_on_until`,t)} ${new Date(m).toLocaleTimeString(t,{hour:`2-digit`,minute:`2-digit`,second:`2-digit`})}</strong></p>`:L}
            `:L}
          `:L}

          ${o>0||r.length>0?this._renderFanSharing(e,i):L}

          ${o>0?F`<div class="alarm-summary">
            ${u?.attributes.fan_nobody_home===!0?F`<strong>${V(`fan.nobody_home`,t)}</strong><br />`:L}
            ${k} ${V(`fan.presence_rule`,t)}
          </div>`:L}
        </div>
        `:this._foldSummary(`fan`,F`
            ${u?.attributes.fan_nobody_home===!0?F`<strong>${V(`fan.nobody_home`,t)}</strong><br />`:L}
            ${o>0?k:V(`fan.none`,t)}`)}
      </div>
    `}_temperatureSensors(e){return U(this.hass,e,`sensor`,[`temperature`])}_renderFanTempFields(e){let t=this.hass.language,n=e.fan_temp_sensor??``,r=e.fan_temp_min??24,i=e.fan_temp_speed??Z.medium,a=n?this.hass.states[n]:void 0,o=a?.attributes.unit_of_measurement??`°C`,s=a&&a.state!==``&&Number.isFinite(Number(a.state))?Number(a.state):null,c=s===null?``:`${new Intl.NumberFormat(t,{maximumFractionDigits:2}).format(s)} ${o}`,l=G(this.hass,e.area_id)?.attributes.fan_temp_active===!0;return F`
      ${n?this._renderSensorRow(n,`mdi:thermometer`,l?`var(--primary-color)`:`var(--secondary-text-color)`,s===null?a?.state??`—`:c,l,()=>this._patch({fan_temp_sensor:``})):this._renderAreaPicker(this._temperatureSensors(e.area_id),V(`fan.temp_pick`,t),V(`fan.temp_none`,t),e=>{let t=e.detail.value;t&&this._patch({fan_temp_sensor:t})})}
      <div class="target-lux-row">
        <span class="fixed-label">${V(`fan.temp_from`,t)}</span>
        <input type="range" min="0" max="50" step="0.5" aria-label=${V(`fan.temp_from`,t)}
          .value=${String(r)}
          @input=${e=>this._patch({fan_temp_min:Number(e.target.value)})} />
        ${this._num(r,-20,80,o,V(`fan.temp_from`,t),e=>this._patch({fan_temp_min:e}),L,.5)}
      </div>
      <div class="target-lux-row">
        <span class="fixed-label">${V(`fan.speed`,t)}</span>
        ${this._fanSpeedButtons(i,V(`fan.speed`,t),e=>this._patch({fan_temp_speed:e}))}
      </div>
      ${n&&s!==null?F`<p class="empty-hint" style="padding: var(--vr-space-1) 0 0"><strong>${l?V(`fan.temp_active`,t).replace(`{temp}`,c):V(`fan.temp_inactive`,t).replace(`{temp}`,c)}</strong></p>`:L}
    `}_toggleDebug(){this._debugOpen=!this._debugOpen,window.clearInterval(this._debugTimer),this._debugTimer=void 0,this._debugOpen&&(this._loadDebug(),this._debugTimer=window.setInterval(()=>void this._loadDebug(),3e3))}async _loadDebug(){if(this.room)try{let e=await this.hass.callWS({type:`roomcontrol/get_debug`,area_id:this.room.area_id});this._debugEntries=e.entries??[],this._debugNow=e.now??null}catch{this._debugEntries=[]}}_debugText(e){let t=this.hass.language,n=(e,n)=>{let r=V(e,t);return r===e?n:r};return[n(`debug.reason.${e.reason.replace(/[^a-z0-9_]+/gi,`_`).toLowerCase()}`,e.reason),e.why?n(`debug.why.${e.why}`,n(`motion_note.${e.why}`,e.why)):``,[e.lux===void 0?``:`${e.lux} lx`,e.target===void 0?``:`${n(`debug.target`,`doel`)} ${e.target} lx`,e.pct===void 0?``:`${e.pct}%`,e.clock?`${n(`debug.clock`,`wekker`)} ${e.clock}`:``,e.schedule?`${n(`debug.schedule`,`schema`)} ${n(`debug.v_${e.schedule}`,e.schedule)}`:``,e.sun?`${n(`debug.sun`,`zon`)} ${n(`debug.v_${e.sun}`,e.sun)}`:``,e.home?`${n(`debug.home`,`thuis`)}: ${n(`debug.v_${e.home}`,e.home)}`:``,e.minutes===void 0?``:`${e.minutes} min`,e.time?`${n(`debug.lock_at`,`om`)} ${e.time}`:``].filter(Boolean).join(` · `)].filter(Boolean).join(` — `)}_renderDebugNow(e){let t=this.hass.language,n=e=>V(e?`debug.v_yes`:`debug.v_no`,t),r=e=>new Date(e).toLocaleString(t,{weekday:`short`,hour:`2-digit`,minute:`2-digit`}),i=[[V(`debug.now_schedule`,t),e.schedule?`${e.schedule} · ${e.schedule_on?V(`debug.v_on`,t):V(`debug.v_off`,t)}`:V(`debug.now_no_schedule`,t)],[V(`debug.now_sun`,t),`${e.sun_entity}: ${e.sun_state??V(`debug.now_missing`,t)} → ${e.sun_down?V(`debug.v_down`,t):V(`debug.v_up`,t)}`],[V(`debug.now_alarm`,t),V(`debug.alarm_${e.alarm}`,t)],[V(`debug.now_home`,t),n(e.someone_home)],[V(`debug.now_manual`,t),n(e.manual)],[V(`debug.now_motion`,t),n(e.motion)],[V(`debug.now_lux`,t),e.lux===null?`—`:`${e.lux} lx · ${V(`debug.now_dark_from`,t)} ${e.dark_from??`—`} · ${V(`debug.target`,t)} ${e.target_lux||V(`debug.v_off`,t)}`]];return F`
      <div class="debug-now">
        <div class="debug-now-title">${V(`debug.now`,t)}</div>
        <div class="debug-now-grid">
          ${i.map(([e,t])=>F`<span class="debug-now-k">${e}</span><span>${t}</span>`)}
        </div>
        ${e.bundles.length?F`
          <div class="debug-now-title" style="margin-top: var(--vr-space-2)">${V(`debug.now_bundles`,t)}</div>
          ${e.bundles.map(e=>F`
            <div class="debug-now-bundle">
              <strong>${e.name}</strong>
              <span class="debug-pill ${e.on?`on`:``}">${e.on?V(`debug.v_on`,t):V(`debug.v_off`,t)}</span>
              <span>${V(`debug.wants_${e.wants}`,t)}</span>
              <span class="debug-flags">${[e.follows_schedule?V(`debug.flag_schedule`,t):V(`debug.flag_no_schedule`,t),e.on_motion?V(`debug.flag_motion`,t):``,e.lux_control?V(`debug.flag_lux`,t):``].filter(Boolean).join(` · `)}</span>
            </div>`)}`:L}
        ${e.locks?.length?F`
          <div class="debug-now-title" style="margin-top: var(--vr-space-2)">${V(`debug.now_locks`,t)}</div>
          ${e.locks.map(e=>F`
            <div class="debug-now-bundle">
              <strong>${e.name}</strong>
              <span class="debug-pill ${e.state===`locked`?``:`on`}">${V(`debug.lock_state.${e.state??`missing`}`,t)||e.state}</span>
              <span>${e.since?`${V(`debug.since`,t)} ${r(e.since)}`:``}</span>
              <span class="debug-flags">${[e.next?`${V(`debug.lock_next`,t)} ${r(e.next)}`:V(`debug.lock_no_times`,t),e.away_lock?V(`debug.lock_away`,t).replace(`{min}`,String(e.away_minutes??5))+(e.nobody_home_since?` (${V(`debug.lock_nobody_since`,t)} ${r(e.nobody_home_since)})`:``):``,e.catch_up?`${V(`debug.lock_catch_up`,t)} ${r(e.catch_up)}`:``].filter(Boolean).join(` · `)}</span>
            </div>`)}`:L}
        ${e.doors?.length?F`
          <div class="debug-now-title" style="margin-top: var(--vr-space-2)">${V(`debug.now_doors`,t)}</div>
          ${e.doors.map(e=>F`
            <div class="debug-now-bundle">
              <strong>${e.name}</strong>
              <span class="debug-pill ${e.state===`on`?`on`:``}">${e.state===`on`?V(`debug.door_open`,t):e.state===`off`?V(`debug.door_closed`,t):e.state??V(`debug.now_missing`,t)}</span>
              <span>${e.since?`${V(`debug.since`,t)} ${r(e.since)}`:``}</span>
            </div>`)}`:L}
      </div>
    `}_renderDebug(){let e=this.hass.language,t={on:`mdi:lightbulb-on-outline`,off:`mdi:lightbulb-off-outline`,adjust:`mdi:tune-vertical`,ignored:`mdi:motion-sensor-off`,blocked:`mdi:cancel`,info:`mdi:information-outline`,lock:`mdi:lock-outline`,door:`mdi:door`};return F`
      <div class="debug-panel" role="log" aria-label=${V(`debug.title`,e)}>
        <div class="debug-head">
          <span class="debug-title"><ha-icon icon="mdi:bug-outline"></ha-icon>${V(`debug.title`,e)}</span>
          <span class="debug-sub">${V(`debug.sub`,e)}</span>
        </div>
        ${this._debugNow?this._renderDebugNow(this._debugNow):L}
        ${this._debugEntries.length===0?F`<p class="empty-hint" style="padding: var(--vr-space-1) 0 0">${V(`debug.empty`,e)}</p>`:F`<div class="debug-list">
              ${this._debugEntries.map(n=>F`
                <div class="debug-row ${n.kind}">
                  <span class="debug-time">${new Date(n.at).toLocaleTimeString(e,{hour:`2-digit`,minute:`2-digit`,second:`2-digit`})}</span>
                  <ha-icon icon=${t[n.kind]??`mdi:circle-small`}></ha-icon>
                  <span class="debug-kind">${V(`debug.kind.${n.kind}`,e)}</span>
                  <span class="debug-text">
                    ${n.bundles.length?F`<strong>${n.bundles.join(`, `)}</strong> · `:L}${n.device?F`<strong>${n.device}</strong> · `:L}${this._debugText(n)}
                  </span>
                </div>`)}
            </div>`}
      </div>
    `}_lateHomeNow(){return Object.values(this.hass.states).filter(e=>e.entity_id.startsWith(`switch.`)&&e.state===`on`&&typeof e.attributes.person==`string`&&(this.settings.late_home_persons??[]).includes(e.attributes.person)).map(e=>{let t=e.attributes.person;return this.hass.states[t]?.attributes.friendly_name??t}).join(`, `)}static{this.LIST_SECTIONS=new Set([`lights`,`locks`,`vacuum`,`smart`])}_isOpen(e){return this._closedSections.has(e)?!1:X.LIST_SECTIONS.has(e)||this._fullSections.has(e)}_shown(e){return!this._closedSections.has(e)}_setFull(e,t){let n=new Set(this._fullSections);if(t?n.add(e):n.delete(e),this._fullSections=n,t&&this._closedSections.has(e)){let t=new Set(this._closedSections);t.delete(e),this._closedSections=t}}_toggleSection(e){let t=new Set(this._closedSections);t.has(e)?t.delete(e):t.add(e),this._closedSections=t}_foldTitle(e,t){let n=this._shown(e),r=n&&this._fullSections.has(e)&&!X.LIST_SECTIONS.has(e),i=this.hass.language;return F`<span class="title-group">
      <button class="fold-btn" aria-expanded=${n?`true`:`false`} @click=${()=>this._toggleSection(e)}>
        <span class="section-title">${t}</span>
        <ha-icon icon=${n?`mdi:chevron-up`:`mdi:chevron-down`}></ha-icon>
      </button>
      ${this._infoBtn(e)}
      ${r?F`<button class="info-btn" title=${V(`fold.less`,i)} aria-label=${V(`fold.less`,i)}
        @click=${()=>this._setFull(e,!1)}><ha-icon icon="mdi:unfold-less-horizontal"></ha-icon></button>`:L}
    </span>`}_infoOpen(e){return this._openInfos.has(e)}_infoBtn(e){let t=this._infoOpen(e),n=this.hass.language;return F`<button
      class="info-btn ${t?`active`:``}"
      aria-pressed=${t?`true`:`false`}
      aria-label=${V(t?`info.hide`:`info.show`,n)}
      title=${V(t?`info.hide`:`info.show`,n)}
      @click=${()=>{let n=new Set(this._openInfos);t?n.delete(e):n.add(e),this._openInfos=n}}
    ><ha-icon icon=${t?`mdi:information`:`mdi:information-outline`}></ha-icon></button>`}_infoText(e,t=L){return this._infoOpen(e)?F`<div class="section-info">
      <p>${V(`info.${e}`,this.hass.language)}</p>
      ${t}
    </div>`:L}_scheduleDimCodes(e){let t=this.hass.language,n=e.groups??[],r=[{code:`dim: true`,what:V(`info.dim_code_all`,t)},...n.flatMap(e=>{let n=un(e.name??``);return n?[{code:`dim_${n}: true`,what:V(`info.dim_code_bundle_name`,t).replace(`{name}`,e.name)}]:[]})];return F`
      <p style="margin-top: var(--vr-space-2)"><strong>${V(`info.dim_codes_title`,t)}</strong>
        ${V(`info.dim_codes_where`,t)}</p>
      <table class="code-table">
        ${r.map(e=>F`<tr><td><code class="schedule-key">${e.code}</code></td><td>${e.what}</td></tr>`)}
      </table>
    `}_foldSummary(e,t){return this._shown(e)?F`<button class="fold-summary" @click=${()=>this._setFull(e,!0)}
      aria-label=${V(`fold.expand`,this.hass.language)}>
      <span class="fold-summary-text">${t}</span>
      <ha-icon icon="mdi:chevron-down"></ha-icon>
    </button>`:L}_entName(e){return this.hass.states[e]?.attributes.friendly_name??e}_when(e){if(!e)return``;let t=new Date(e),n=new Date().toDateString()===t.toDateString();return t.toLocaleString(this.hass.language,n?{hour:`2-digit`,minute:`2-digit`}:{weekday:`short`,hour:`2-digit`,minute:`2-digit`})}_battery(e){let t=bt(this.hass,e),n=t?this.hass.states[t]:void 0;if(!t||!n)return null;if(t.startsWith(`binary_sensor.`))return n.state===`on`?{text:V(`fold.battery_low`,this.hass.language),low:!0}:null;let r=Number(n.state);return isNaN(r)?null:{text:`${Math.round(r)}%`,low:r<20}}_foldItems(e,t,n){if(!this._shown(e))return L;let r=this.hass.language;return t.length?F`<div class="item-cards">
      ${t.map(t=>F`
        <button class="item-card" @click=${()=>this._setFull(e,!0)} aria-label="${t.title} · ${V(`fold.expand`,r)}">
          <ha-icon class="item-icon ${t.tone??``}" icon=${t.icon}></ha-icon>
          <span class="item-text">
            <span class="item-title">${t.title}</span>
            ${t.pills?.length?F`<span class="item-pills">${t.pills.map(e=>F`<span class="item-pill">${e}</span>`)}</span>`:L}
          </span>
          ${t.status?F`<span class="item-status ${t.tone??``}">${t.status}</span>`:L}
          <ha-icon class="item-chev" icon="mdi:chevron-down"></ha-icon>
        </button>`)}
    </div>`:this._foldSummary(e,n)}_renderFanSharing(e,t){let n=this.hass.language,r=e.fan_shared_rooms??[],i=e=>{this._draft&&={...this._draft,fan_shared_rooms:e}};return F`
      <div class="alarm-sub">${V(`fan.share_title`,n)}</div>
      <div class="chip-row">
        ${r.map(e=>F`
          <span class="chip">
            <ha-icon icon="mdi:link-variant"></ha-icon>${this._areaName(e)}
            <button class="chip-x" aria-label="${V(`common.remove`,n)}: ${this._areaName(e)}"
              @click=${()=>i(r.filter(t=>t!==e))}>
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
          </span>
        `)}
        ${this._addingFanShare?L:F`
          <button class="chip chip-add" @click=${()=>{this._fanShareSelection=new Set,this._addingFanShare=!0}}>
            <ha-icon icon="mdi:plus"></ha-icon>${V(`fan.share_add`,n)}
          </button>`}
      </div>
      ${this._addingFanShare?this._renderMultiChooser({available:Je(this.hass,this.allRooms).map(e=>e.area_id).filter(t=>t!==e.area_id&&!r.includes(t)),selected:()=>this._fanShareSelection,icon:()=>`mdi:link-variant`,name:e=>this._areaName(e),emptyText:V(`room.links_none_available`,n),onChange:e=>{this._fanShareSelection=e},onCancel:()=>{this._addingFanShare=!1},onConfirm:e=>{i([...r,...e.filter(e=>!r.includes(e))]),this._addingFanShare=!1,this._fanShareSelection=new Set}}):L}
      <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">
        <span class="info-text">${r.length>0?V(`fan.share_hint`,n):V(`fan.share_none`,n)}</span>
        ${t.length>r.length?F`<br />${V(`room.links_group`,n)}: ${t.map(e=>this._areaName(e)).join(`, `)}`:L}
      </p>
    `}_fanLevel(e){let t=[`low`,`medium`,`high`];return t.reduce((t,n)=>Math.abs(Z[n]-e)<=Math.abs(Z[t]-e)?n:t,t[0])}_renderFanStatus(e){let t=this.hass.language,n=[...(e.fans??[])];for(let r of $e(this.allRooms,e,`fan_shared_rooms`))for(let i of this.allRooms.find(e=>e.area_id===r)?.fans??[])i&&!n.includes(i)&&n.push(i);if(n.length===0)return L;let r=n.map(e=>this.hass.states[e]).find(e=>e?.state===`on`),i=r?.attributes.percentage,a=G(this.hass,e.area_id)?.attributes??{},o=a.fan_step,s=a.fan_step_count,c=a.fan_off_at,l=[];r?(typeof i==`number`&&i>0?l.push(`${V(`fan.level_${this._fanLevel(i)}`,t)} · ${i}%`):l.push(V(`card.on`,t)),typeof o==`number`&&o>0&&typeof s==`number`&&s>0&&l.push(V(`fan.status_step`,t).replace(`{n}`,String(o)).replace(`{total}`,String(s))),c&&l.push(`${V(`fan.status_until`,t)} ${new Date(c).toLocaleTimeString(t,{hour:`2-digit`,minute:`2-digit`})}`)):l.push(V(`fan.status_off`,t));return F`
          <div class="master-row" style="font-size: var(--vr-font-sm); color: ${r?`var(--primary-text-color)`:`var(--secondary-text-color)`};">
            <ha-icon icon=${r?`mdi:fan`:`mdi:fan-off`} style="--mdc-icon-size:16px"></ha-icon>
            ${V(`fan.status_label`,t)}: ${l.join(` · `)}
          </div>
        `}_renderMotionWindow(e,n){let t=this.hass.language,r=e.motion_windows?.[n]??{},i=!!(r.start&&r.end),a=(a,o)=>{let s={...e.motion_windows??{}},c={...s[n]??{},[a]:o||void 0};c.start||c.end?s[n]=c:delete s[n],this._patch({motion_windows:s})},o=()=>{let t={...e.motion_windows??{}};delete t[n],this._patch({motion_windows:t})};return F`
          <div class="motion-window" style="display:flex; align-items:center; flex-wrap:wrap; gap:var(--vr-space-2); padding:0 0 var(--vr-space-2) var(--vr-space-4); font-size:var(--vr-font-sm); color:var(--secondary-text-color);">
            <ha-icon icon="mdi:clock-outline" style="--mdc-icon-size:16px"></ha-icon>
            <span>${V(`motion_window.label`,t)}</span>
            <input type="time" aria-label=${`${V(`motion_window.label`,t)} (${this._entName(n)})`} .value=${r.start??``} @change=${e=>a(`start`,e.target.value)} />
            <span>${V(`motion_window.until`,t)}</span>
            <input type="time" aria-label=${`${V(`motion_window.until`,t)} (${this._entName(n)})`} .value=${r.end??``} @change=${e=>a(`end`,e.target.value)} />
            ${i?F`<button class="retry-link" @click=${o}>${V(`motion_window.clear`,t)}</button>`:F`<span>(${V(`motion_window.always`,t)})</span>`}
          </div>
        `}_renderCoversOpenAt(e){let t=this.hass.language,r=`never`,i=[`light`,`time`].includes(e.covers_open_at)?e.covers_open_at:r,a=[[r,`mdi:minus-circle-outline`],[`light`,`mdi:weather-sunset-up`],[`time`,`mdi:clock-outline`]];return F`
              <div class="alarm-sub">${V(`covers.open_at`,t)}</div>
              <div class="alarm-options" role="radiogroup" aria-label=${V(`covers.open_at`,t)}>
                ${a.map(([n,r])=>F`
                  <button class="alarm-opt ${i===n?`selected`:``}" role="radio"
                    aria-checked=${i===n?`true`:`false`}
                    @click=${()=>this._patch(n===`light`?{covers_open_at:`light`}:n===`time`?{covers_open_at:`time`,covers_open_time:e.covers_open_time??`07:00`}:{covers_open_at:void 0})}>
                    <ha-icon icon=${r}></ha-icon>
                    <span class="alarm-opt-title">${V(`covers.open_at_${n}`,t)}</span>
                  </button>`)}
              </div>
              ${i===`time`?F`<div class="target-lux-row">
                <ha-icon icon="mdi:clock-outline"></ha-icon>
                <input type="time" aria-label=${V(`covers.open_at_time`,t)} .value=${e.covers_open_time??`07:00`}
                  @change=${e=>e.target.value&&this._patch({covers_open_time:e.target.value})} />
              </div>`:L}
              <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">${V(`covers.open_at_${i}_hint`,t)}</p>
        `}_fanLevelName(e){return V(`fan.level_${this._fanLevel(e)}`,this.hass.language).toLowerCase()}_fanSpeedButtons(e,t,n){let r=this.hass.language,i=e>0?this._fanLevel(e):null;return F`<div class="segmented fan-speed-seg" role="radiogroup" aria-label=${t}>
      ${[`low`,`medium`,`high`].map(e=>F`
        <button
          role="radio"
          aria-checked=${i===e?`true`:`false`}
          class=${i===e?`active`:``}
          title="${Z[e]}%"
          @click=${()=>n(Z[e])}
        >${V(`fan.level_${e}`,r)}</button>`)}
    </div>`}_addFanStep(){if(!this._draft)return;let e=this._draft.fan_steps??[],t=e.reduce((e,t)=>!e||t.minutes>e.minutes?t:e,null),n=[Z.low,Z.medium,Z.high],r=t?{minutes:t.minutes+5,percentage:n.find(e=>e>t.percentage)??Z.high}:{minutes:5,percentage:Z.low};this._patch({fan_steps:[...e,r]})}_setFanStep(e,t){if(!this._draft)return;let n=(this._draft.fan_steps??[]).map((n,r)=>r===e?{...n,...t}:n);`minutes`in t&&n.sort((e,t)=>e.minutes-t.minutes),this._patch({fan_steps:n})}_coverInverted(e){return(this._draft?.covers_inverted??this.room.covers_inverted??[]).includes(e)}_coverState(e){let t=this.hass.states[e];if(!t)return null;let n={open:`closed`,closed:`open`,opening:`closing`,closing:`opening`},r=this._coverInverted(e),i=t.attributes.current_position;return{state:r?n[t.state]??t.state:t.state,pos:typeof i==`number`?r?100-i:i:void 0}}_coverStateText(e){let t=this.hass.language,n=this._coverState(e);if(!n)return`—`;let r=[`open`,`closed`,`opening`,`closing`].includes(n.state)?n.state:null,i=r?V(`covers.state_${r}`,t):n.state;return n.pos!==void 0&&n.state===`open`&&n.pos<100?`${i} ${n.pos}%`:i}async _testCover(e){await this._flushSave(),this._coverTest={id:e,phase:`running`};try{await Ke(this.hass,[e],`open_cover`),await new Promise(e=>window.setTimeout(e,3e3)),await Ke(this.hass,[e],`stop_cover`)}finally{this._coverTest?.id===e&&(this._coverTest={id:e,phase:`ask`})}}_setCoverInverted(e,t){let n=this._draft?.covers_inverted??[],r=t?[...new Set([...n,e])]:n.filter(t=>t!==e);this._patch({covers_inverted:r})}_renderCoverRow(e,t){let n=this.hass.language,r=this._coverState(e),i=this.hass.states[e]?.attributes.friendly_name??e,a=this._openCovers.has(e),o=this._coverInverted(e),s=this._coverTest?.id===e?this._coverTest.phase:null;return F`
      <div class="cover-row ${a?`open`:``}">
        <div class="cover-row-head">
          <ha-icon icon=${r?.state===`closed`?`mdi:curtains-closed`:`mdi:curtains`}
            style="color: ${a?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
          <button class="cover-row-btn" aria-expanded=${a?`true`:`false`} @click=${()=>{let t=new Set(this._openCovers);a?t.delete(e):t.add(e),this._openCovers=t}}>
            <span class="light-entity" title=${e}>${i}${o?F` <span class="cover-chip">${V(`covers.inverted_chip`,n)}</span>`:L}</span>
            <span class="light-state">${this._coverStateText(e)}</span>
            <ha-icon icon=${a?`mdi:chevron-up`:`mdi:chevron-down`}></ha-icon>
          </button>
          ${this._moveCtl(t)}
          <ha-icon-button
            class="remove-btn"
            .label=${V(`common.remove`,n)}
            .path=${`M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z`}
            @click=${()=>this._removeCover(e)}
          ></ha-icon-button>
        </div>
        ${a?F`
          <div class="cover-row-body">
            <div class="cover-follow">
              <ha-icon icon="mdi:swap-vertical" style="--mdc-icon-size:20px; flex: none; color: ${o?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
              <div class="dusk-text">
                <div class="dusk-title">${V(`covers.inverted`,n)}</div>
                <div class="alarm-opt-hint">${V(o?`covers.inverted_on`:`covers.inverted_off`,n)}</div>
              </div>
              <vr-toggle .checked=${o} @change=${t=>this._setCoverInverted(e,t.detail.value)}></vr-toggle>
            </div>
            <div class="cover-follow">
              <ha-icon icon="mdi:play-circle-outline" style="--mdc-icon-size:20px; flex: none; color: var(--secondary-text-color)"></ha-icon>
              <div class="dusk-text">
                <div class="dusk-title">${V(`covers.test`,n)}</div>
                <div class="alarm-opt-hint">${V(s===`running`?`covers.test_running`:`covers.test_hint`,n)}</div>
              </div>
              <button class="chooser-btn" ?disabled=${s===`running`} @click=${()=>this._testCover(e)}>
                <ha-icon icon="mdi:play"></ha-icon>${V(`covers.test_btn`,n)}
              </button>
            </div>
            ${s===`ask`?F`
              <div class="cover-ask" role="group" aria-label=${V(`covers.test_question`,n)}>
                <div class="dusk-title">${V(`covers.test_question`,n)}</div>
                <div class="cover-ask-btns">
                  <button class="chooser-btn" @click=${()=>{this._coverTest=null}}>
                    <ha-icon icon="mdi:check"></ha-icon>${V(`covers.test_yes`,n)}
                  </button>
                  <button class="chooser-btn" @click=${()=>{this._setCoverInverted(e,!o),this._coverTest=null}}>
                    <ha-icon icon="mdi:swap-vertical"></ha-icon>${V(`covers.test_no`,n)}
                  </button>
                </div>
              </div>`:L}
          </div>`:L}
      </div>
    `}_renderLocks(e){let t=this.hass.language,n=(e.locks??[]).filter(e=>e.entity_id),r=U(this.hass,e.area_id,`lock`);if(n.length===0&&r.length===0)return L;let i=n.map(e=>e.entity_id),a=e=>this._patch({locks:e}),o=(e,t)=>a(n.map(n=>n.entity_id===e?{...n,...t}:n)),s=i.filter(e=>this.hass.states[e]?.state===`locked`).length,c=n.length===0?V(`locks.none`,t):V(`locks.fold`,t).replace(`{n}`,String(n.length)).replace(`{locked}`,String(s));return F`
      <div class="section ${this._infoOpen(`locks`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`locks`,V(`locks.section`,t))}
          ${this._shown(`locks`)?F`<button class="add-btn" @click=${()=>{this._setFull(`locks`,!0),this._lockSelection=new Set,this._addingLocks=!0}}>
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>
            ${V(`locks.add`,t)}
          </button>`:L}
        </div>
        ${this._infoText(`locks`)}
        ${this._isOpen(`locks`)?F`
          ${n.length===0&&!this._addingLocks?F`<p class="empty-hint">${V(`locks.none`,t)}</p>`:L}
          ${this._addingLocks?this._renderMultiChooser({available:r.filter(e=>!i.includes(e)),selected:()=>this._lockSelection,icon:()=>`mdi:lock`,emptyText:V(`locks.none_in_area`,t),onChange:e=>{this._lockSelection=e},onCancel:()=>{this._addingLocks=!1},onConfirm:e=>{a([...n,...e.map(e=>({entity_id:e,slots:[],confirm_open:!0}))]),this._openLocks=new Set([...this._openLocks,...e]),this._addingLocks=!1}}):L}
          <div class="group-list">
            ${n.map(e=>this._renderLock(e,t=>o(e.entity_id,t),()=>a(n.filter(t=>t.entity_id!==e.entity_id))))}
          </div>
          ${n.length>0?F`<p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`locks.hint`,t)}</p>`:L}
        `:this._foldSummary(`locks`,c)}
      </div>
    `}_renderLock(e,t,n){let r=this.hass.language,i=e.entity_id,a=this.hass.states[i],o=a?.state??`unavailable`,s=o===`locked`,c=o===`unlocked`||o===`open`,l=a?.attributes.friendly_name??i,u=this._openLocks.has(i),d=()=>{let e=new Set(this._openLocks);u?e.delete(i):e.add(i),this._openLocks=e},f=e.confirm_open!==!1,p=()=>{f&&this._confirmLock!==i?this._confirmLock=i:(this._confirmLock=null,H(this.hass,`lock`,`unlock`,{entity_id:i}))},m=()=>{this._confirmLock=null,H(this.hass,`lock`,`lock`,{entity_id:i})},h=a?.last_changed?new Date(a.last_changed).toLocaleString(r,{weekday:`short`,hour:`2-digit`,minute:`2-digit`}):``,g=V(s?`locks.state_locked`:c?`locks.state_open`:o===`jammed`?`locks.state_jammed`:o===`locking`||o===`unlocking`?`locks.state_moving`:`locks.state_unknown`,r),_=e.slots_enabled===!1,v=(e.slots??[]).map(e=>_?{...e,enabled:e.enabled??!1}:e),y=v.filter(e=>e.enabled!==!1),b=e.away_minutes??5,x=[...y.length?y.map(e=>this._clockPill(e.holiday===`vacation`?`mdi:palm-tree`:`mdi:lock-clock`,`${dn(e)} · ${this._lockTimeSummary(e).split(` · `)[0]}`)):[this._clockPill(`mdi:calendar-remove-outline`,V(v.length?`locks.pill_slots_off`:`locks.pill_no_slots`,r),`off`)],e.away_lock?this._clockPill(`mdi:home-export-outline`,V(`locks.pill_away`,r).replace(`{min}`,String(b)),`light`):L,f?this._clockPill(`mdi:shield-check-outline`,V(`locks.pill_confirm`,r),`cover`):L];return F`
      <div class="bundle-card ${u?`open`:``}">
        <div class="bundle-row ${u?`open`:``}" @click=${u?L:d}>
          <ha-icon class="bundle-icon lock-icon ${s?`locked`:c?`unlocked`:``}"
            icon=${s?`mdi:lock`:c?`mdi:lock-open-variant`:o===`jammed`?`mdi:lock-alert`:`mdi:lock-question`}></ha-icon>
          <div class="bundle-text">
            <span class="bundle-title">${l}</span>
            ${u?F`<span class="bundle-sub">${i}${h?` · ${V(`locks.since`,r)} ${h}`:``}</span>`:F`<span class="lock-pills">${x}</span>`}
          </div>
          <span class="lock-state ${s?`locked`:c?`unlocked`:``}">${g}</span>
          <button class="chooser-btn lock-btn" @click=${e=>{e.stopPropagation(),s?p():m()}}>
            <ha-icon icon=${s?`mdi:lock-open-variant-outline`:`mdi:lock-outline`}></ha-icon>
            ${V(s?`locks.open`:`locks.lock`,r)}
          </button>
          <button class="bundle-expand" aria-expanded=${u?`true`:`false`}
            aria-label=${V(u?`bundles.collapse`:`bundles.expand`,r)}
            @click=${e=>{e.stopPropagation(),d()}}>
            <ha-icon icon=${u?`mdi:chevron-up`:`mdi:chevron-down`}></ha-icon>
          </button>
        </div>
        ${this._confirmLock===i?F`
          <div class="lock-confirm" role="alertdialog" aria-label=${V(`locks.confirm_q`,r).replace(`{name}`,l)}>
            <span><ha-icon icon="mdi:alert-outline"></ha-icon>${V(`locks.confirm_q`,r).replace(`{name}`,l)}</span>
            <span class="lock-confirm-acts">
              <button class="chooser-btn" @click=${()=>{this._confirmLock=null}}>${V(`locks.cancel`,r)}</button>
              <button class="chooser-btn danger" @click=${p}>
                <ha-icon icon="mdi:lock-open-variant-outline"></ha-icon>${V(`locks.confirm_yes`,r)}</button>
            </span>
          </div>`:L}
        ${u?F`
          <div class="bundle-body">
            ${this._renderLockTimes(v,e=>t({slots:e,slots_enabled:void 0}),`lock:${i}`)}

            <div class="alarm-sub">${V(`locks.options`,r)}</div>
            <div class="cover-follow" style="margin-top: 0; padding-top: 0; border-top: none">
              <ha-icon icon="mdi:home-export-outline" style="--mdc-icon-size:20px; flex: none; color: ${e.away_lock?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
              <div class="dusk-text">
                <div class="dusk-title">${V(`locks.away`,r)}</div>
                <div class="alarm-opt-hint">${V(`locks.away_hint`,r).replace(`{min}`,String(b))}</div>
              </div>
              ${e.away_lock?F`<span style="flex: none">
                ${this._num(b,0,240,`min`,V(`locks.away_after`,r),e=>t({away_minutes:e}))}</span>`:L}
              <vr-toggle .checked=${!!e.away_lock} @change=${e=>t({away_lock:e.detail.value})}></vr-toggle>
            </div>
            <div class="cover-follow">
              <ha-icon icon="mdi:shield-check-outline" style="--mdc-icon-size:20px; flex: none; color: ${f?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
              <div class="dusk-text">
                <div class="dusk-title">${V(`locks.confirm`,r)}</div>
                <div class="alarm-opt-hint">${V(`locks.confirm_hint`,r)}</div>
              </div>
              <vr-toggle .checked=${f} @change=${e=>t({confirm_open:e.detail.value})}></vr-toggle>
            </div>
            <div class="alarm-summary">
              ${V(`locks.never_opens`,r)}
              <button class="link-btn danger-link" @click=${n}>${V(`locks.remove`,r)}</button>
            </div>
          </div>`:L}
      </div>
    `}_renderLockTimes(e,t,n){let r=this.hass.language,i=[0,1,2,3,4,5,6].map(e=>V(`clock.day_${e}`,r)),a=(n,r)=>t(e.map((e,t)=>t===n?{...e,...r}:e)),o=Object.keys(this.hass.states).find(e=>e.startsWith(`switch.`)&&this.hass.states[e].attributes.roomcontrol_vacation===!0),s=o?this.hass.states[o].state===`on`:!1;return F`
      <div class="alarm-sub">${V(`locks.times_title`,r)}${o?F` <span class="alarm-tab-now">· ${V(s?`slots.vacation_on`:`slots.vacation_off`,r)}</span>`:L}</div>
      ${e.length===0?F`<p class="empty-hint" style="padding: 0">${V(`locks.times_none`,r)}</p>`:L}
      <div class="slot-list">
        ${e.map((o,s)=>{let c=dn(o),l=o.enabled!==!1,u=F`<vr-toggle .checked=${l} aria-label=${V(`locks.time_on`,r)}
            @change=${e=>a(s,{enabled:e.detail.value?void 0:!1})}></vr-toggle>`;return this._openSlots.has(`${n}:${s}`)?F`
          <div class="slot-row ${l?``:`slot-off`}">
            <div class="slot-head">
              <input class="clock-input slot-name" .value=${o.name??``}
                placeholder="${V(`locks.time_name_placeholder`,r)} ${s+1}"
                aria-label=${V(`slots.name`,r)}
                @input=${e=>a(s,{name:e.target.value})} />
              ${u}
              <button class="bundle-expand" aria-expanded="true" aria-label=${V(`bundles.collapse`,r)}
                @click=${()=>{let e=new Set(this._openSlots);e.delete(`${n}:${s}`),this._openSlots=e}}>
                <ha-icon icon="mdi:chevron-up"></ha-icon>
              </button>
            </div>
            <div class="slot-days-row">
              <div class="chip-row slot-days">
                ${i.map((e,t)=>F`
                  <button class="chip chip-day ${o.days.includes(t)?`on`:``}" role="checkbox"
                    aria-checked=${o.days.includes(t)?`true`:`false`}
                    @click=${()=>a(s,{days:o.days.includes(t)?o.days.filter(e=>e!==t):[...o.days,t].sort()})}>
                    ${e}</button>`)}
              </div>
            </div>
            <div class="slot-times">
              <span class="slot-until">${V(`locks.time_at`,r)}</span>
              <input type="time" class="clock-input" .value=${c}
                aria-label=${V(`locks.time_at`,r)}
                @change=${e=>{let t=e.target.value;t&&a(s,{time:t,start:void 0,end:void 0})}} />
              <span style="flex: 1"></span>
              <select class="clock-input" aria-label=${V(`slots.holiday`,r)}
                @change=${e=>a(s,{holiday:e.target.value})}>
                ${[`normal`,`vacation`].map(e=>F`<option value=${e} ?selected=${(o.holiday===`vacation`?`vacation`:`normal`)===e}>${V(`slots.holiday_${e}`,r)}</option>`)}
              </select>
              <ha-icon-button
                class="remove-btn"
                .label=${V(`common.remove`,r)}
                .path=${`M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z`}
                @click=${()=>t(e.filter((e,t)=>t!==s))}
              ></ha-icon-button>
            </div>
          </div>`:F`
          <div class="slot-row slot-folded-wrap ${l?``:`slot-off`}">
            <button class="slot-folded" aria-expanded="false"
              @click=${()=>{this._openSlots=new Set([...this._openSlots,`${n}:${s}`])}}>
              <ha-icon icon=${o.holiday===`vacation`?`mdi:palm-tree`:`mdi:lock-clock`}></ha-icon>
              <span class="slot-folded-text">
                <span class="slot-folded-name">${o.name||`${V(`locks.time_name_placeholder`,r)} ${s+1}`}</span>
                <span class="slot-folded-sub">${l?``:`${V(`locks.time_off`,r)} · `}${this._lockTimeSummary(o)}</span>
              </span>
              <ha-icon icon="mdi:chevron-down"></ha-icon>
            </button>
            ${u}
          </div>`})}
      </div>
      <button class="add-btn" style="margin-top: var(--vr-space-2)"
        @click=${()=>{this._openSlots=new Set([...this._openSlots,`${n}:${e.length}`]),t([...e,{days:[0,1,2,3,4,5,6],time:`22:00`}])}}>
        <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>${V(`locks.time_add`,r)}
      </button>
      <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`locks.times_hint`,r)} ${V(`slots.holiday_hint`,r)}</p>
    `}_lockTimeSummary(e){let t=this.hass.language,n=[0,1,2,3,4,5,6].map(e=>V(`clock.day_${e}`,t));return[e.days.length===7?V(`clock.every_day`,t):[...e.days].sort().map(e=>n[e]).join(`, `)||V(`clock.no_days`,t),dn(e),e.holiday===`vacation`?V(`slots.holiday_vacation`,t).toLowerCase():``].filter(Boolean).join(` · `)}_renderCovers(e){let t=this.hass.language,n=e.covers??[];return n.length===0&&U(this.hass,e.area_id,`cover`).length===0?L:F`
      <div class="section ${this._infoOpen(`covers`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`covers`,V(`covers.section`,t))}
          ${this._shown(`covers`)?F`<button class="add-btn" @click=${()=>{this._setFull(`covers`,!0),this._coverSelection=new Set,this._addingCovers=!0}}>
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>
            ${V(`covers.add`,t)}
          </button>`:L}
        </div>
        ${this._infoText(`covers`)}
        ${this._isOpen(`covers`)?F`

        ${n.length===0?this._addingCovers?L:F`<p class="empty-hint">${V(`covers.none`,t)}</p>`:F`<div class="light-list">
              ${n.map((e,t)=>this._renderCoverRow(e,this._mover(n,t,e=>this._patch({covers:e}))))}
            </div>`}

        ${(e.covers??[]).length>0?this._renderHaName(e,`covers_name`,V(`ha_name.covers_default`,this.hass.language),`mdi:curtains`):L}

        ${this._addingCovers?this._renderMultiChooser({available:U(this.hass,e.area_id,`cover`).filter(e=>!n.includes(e)),selected:()=>this._coverSelection,icon:()=>`mdi:curtains`,emptyText:V(`covers.none_in_area`,t),onChange:e=>{this._coverSelection=e},onCancel:()=>{this._addingCovers=!1},onConfirm:e=>{this._patch({covers:[...n,...e]}),this._addingCovers=!1}}):L}

        ${n.length>0?F`
          <div class="picker-card" style="margin-top: var(--vr-space-2)">
            <div class="cover-buttons" role="group" aria-label=${V(`covers.section`,t)}>
              <button class="chooser-btn" @click=${()=>Ke(this.hass,n,`open_cover`)}>
                <ha-icon icon="mdi:arrow-up"></ha-icon>${V(`covers.open`,t)}
              </button>
              <button class="chooser-btn" @click=${()=>Ke(this.hass,n,`stop_cover`)}>
                <ha-icon icon="mdi:stop"></ha-icon>${V(`covers.stop`,t)}
              </button>
              <button class="chooser-btn" @click=${()=>Ke(this.hass,n,`close_cover`)}>
                <ha-icon icon="mdi:arrow-down"></ha-icon>${V(`covers.close`,t)}
              </button>
            </div>
            <div class="cover-follow">
              <div class="dusk-text">
                <div class="dusk-title">${V(`covers.follow_title`,t)}</div>
                <div class="dusk-hint">
                  ${V(`covers.follow_hint`,t)}
                </div>
              </div>
              <vr-toggle
                .checked=${!!e.covers_follow}
                @change=${e=>this._patch({covers_follow:e.detail.value})}
              ></vr-toggle>
            </div>
            ${e.covers_follow?F`
              <div class="alarm-sub">${V(`covers.close_at`,t)}</div>
              <div class="alarm-options" role="radiogroup" aria-label=${V(`covers.close_at`,t)}>
                ${[[`dusk`,`mdi:weather-sunset-down`],[`dark`,`mdi:weather-night`]].map(([n,r])=>F`
                  <button class="alarm-opt ${(e.covers_close_at??`dark`)===n?`selected`:``}" role="radio"
                    aria-checked=${(e.covers_close_at??`dark`)===n?`true`:`false`}
                    @click=${()=>this._patch({covers_close_at:n})}>
                    <ha-icon icon=${r}></ha-icon>
                    <span class="alarm-opt-title">${V(`covers.close_at_${n}`,t)}</span>
                  </button>`)}
              </div>
              ${this._renderCoversOpenAt(e)}`:L}
          </div>
        `:L}
        `:this._foldItems(`covers`,n.map(n=>{let r=this.hass.states[n],i=r?.attributes.current_position,a=r?.state===`open`||r?.state===`opening`;return{icon:a?`mdi:blinds-open`:`mdi:blinds`,title:this._entName(n),pills:[typeof i==`number`?`${i}%`:``,e.covers_follow?V(`fold.covers_follow`,t):V(`fold.covers_manual`,t)].filter(Boolean),status:!r||r.state===`unavailable`?V(`fold.unavailable`,t):V(a?`door.open`:`door.closed`,t),tone:!r||r.state===`unavailable`?`warn`:a?`on`:``}}),V(`covers.none`,t))}
      </div>
    `}_removeCover(e){this._draft&&={...this._draft,covers:(this._draft.covers??[]).filter(t=>t!==e),covers_inverted:(this._draft.covers_inverted??[]).filter(t=>t!==e)}}_mediaPlaying(e){return this.hass.states[e]?.state===`playing`}_mediaStateText(e){let t=this.hass.language,n=this.hass.states[e];if(!n)return`—`;let r=[`playing`,`paused`,`idle`,`on`,`off`,`standby`,`buffering`,`unavailable`].includes(n.state)?V(`media.state_${n.state}`,t):n.state,i=n.attributes.media_title,a=[n.attributes.media_artist,i].filter(Boolean).join(` – `);return a&&[`playing`,`paused`].includes(n.state)?`${r} · ${a}`:r}_mediaIcon(e){let t=String(this.hass.states[e]?.attributes.device_class??``);return t===`tv`?`mdi:television`:t===`speaker`?`mdi:speaker`:t===`receiver`?`mdi:audio-video`:`mdi:cast`}_renderMediaRow(e,t,n){let r=this.hass.language,i=this.hass.states[e],a=i?.attributes.friendly_name??e,o=this._mediaPlaying(e),s=!!i&&![`unavailable`,`unknown`].includes(i.state);return F`
      <div class="light-row">
        <ha-icon icon=${this._mediaIcon(e)}
          style="color: ${o?`var(--vr-on)`:`var(--secondary-text-color)`}"></ha-icon>
        <span class="light-entity" title=${e}>${a}</span>
        <span class="light-state media-state ${o?`active`:``}">${this._mediaStateText(e)}</span>
        ${s?F`<ha-icon-button
          .label=${V(o?`media.pause`:`media.play`,r)}
          .path=${o?`M14,19H18V5H14M6,19H10V5H6V19Z`:`M8,5.14V19.14L19,12.14L8,5.14Z`}
          @click=${()=>this.hass.callService(`media_player`,`media_play_pause`,{entity_id:e})}
        ></ha-icon-button>`:L}
        ${this._moveCtl(n)}
        <ha-icon-button
          class="remove-btn"
          .label=${V(`common.remove`,r)}
          .path=${`M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z`}
          @click=${t}
        ></ha-icon-button>
      </div>
    `}_renderMedia(e){let t=this.hass.language,n=e.media_players??[];return n.length===0&&U(this.hass,e.area_id,`media_player`).length===0?L:F`
      <div class="section ${this._infoOpen(`media`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`media`,V(`media.section`,t))}
          ${this._shown(`media`)?F`<button class="add-btn" @click=${()=>{this._setFull(`media`,!0),this._mediaSelection=new Set,this._addingMedia=!0}}>
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>
            ${V(`media.add`,t)}
          </button>`:L}
        </div>
        ${this._infoText(`media`)}
        ${this._isOpen(`media`)?F`
          ${n.length===0?this._addingMedia?L:F`<p class="empty-hint">${V(`media.none`,t)}</p>`:F`<div class="light-list">
                ${n.map((e,t)=>this._renderMediaRow(e,()=>this._patch({media_players:n.filter(t=>t!==e)}),this._mover(n,t,e=>this._patch({media_players:e}))))}
              </div>`}
          ${n.length>0?(()=>{let r=e.announce_off??[],i=(e.persons??[]).filter(e=>this.enabledPersons.includes(e)),a=e=>this.hass.states[e]?.attributes.friendly_name??e,o=i.length===0||i.some(e=>this.hass.states[e]?.state===`home`);return F`
              <div class="alarm-sub">${V(`announce.room_title`,t)}</div>
              ${n.map((e,n)=>{let i=!r.includes(e);return F`
                  <div class="cover-follow" style=${n===0?`margin-top: 0; padding-top: 0; border-top: none`:``}>
                    <ha-icon icon="mdi:bullhorn-outline" style="--mdc-icon-size:20px; flex: none; color: ${i?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
                    <div class="dusk-text">
                      <div class="dusk-title">${this.hass.states[e]?.attributes.friendly_name??e}</div>
                    </div>
                    <vr-toggle .checked=${i} aria-label=${V(`announce.room_title`,t)}
                      @change=${t=>{let n=t.detail.value?r.filter(t=>t!==e):[...r,e];this._patch({announce_off:n.length?n:void 0})}}></vr-toggle>
                  </div>`})}
              <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">
                ${i.length===0?V(`announce.room_no_persons`,t):V(o?`announce.room_persons_home`:`announce.room_persons_away`,t).replace(`{names}`,i.map(a).join(`, `))}
              </p>`})():L}
          ${this._addingMedia?this._renderMultiChooser({available:U(this.hass,e.area_id,`media_player`).filter(e=>!n.includes(e)),selected:()=>this._mediaSelection,icon:e=>this._mediaIcon(e),emptyText:V(`media.none_in_area`,t),onChange:e=>{this._mediaSelection=e},onCancel:()=>{this._addingMedia=!1},onConfirm:e=>{this._patch({media_players:[...new Set([...n,...e])]}),this._addingMedia=!1}}):L}
        `:this._foldItems(`media`,n.map(n=>({icon:this._mediaIcon(n),title:this._entName(n),pills:(e.announce_off??[]).includes(n)?[]:[V(`announce.room_title`,t)],status:this._mediaStateText(n),tone:this._mediaPlaying(n)?`on`:``})),V(`media.none`,t))}
      </div>
    `}_sameDevice(e,t){let n=this.hass.entities?.[e]?.device_id;return n?Object.values(this.hass.entities).filter(e=>e.device_id===n&&e.entity_id.startsWith(`${t}.`)&&this.hass.states[e.entity_id]).map(e=>e.entity_id).sort():[]}_renderDoorbell(e){let t=this.hass.language,n=e.doorbell,r=e=>{let t=this.hass.states[e];return t?e.startsWith(`event.`)?t.attributes.device_class===`doorbell`||(t.attributes.event_types??[]).includes(`ring`):e.startsWith(`binary_sensor.`)&&/doorbell|deurbel/i.test(e):!1},i=[...U(this.hass,e.area_id,`event`),...U(this.hass,e.area_id,`binary_sensor`)].filter(r);if(!n&&i.length===0)return L;let a=e=>this.hass.states[e]?.attributes.friendly_name??e,o=e=>{if(!n)return;let t={...n,...e};for(let e of Object.keys(t))t[e]===void 0&&delete t[e];this._patch({doorbell:t})},s=e=>{if(!e){this._patch({doorbell:void 0});return}let t=this._sameDevice(e,`camera`)[0],r=[...this._sameDevice(e,`select`),...this._sameDevice(e,`text`)].find(e=>/doorbell|text|lcd|message|bericht/i.test(e));this._patch({doorbell:{...n??{},entity:e,...t?{camera:t}:{},...r?{away_message:{entity:r,value:n?.away_message?.value??``}}:{}}})},c=[...new Set([...n?[n.entity]:[],...i])],l=n?this.hass.states[n.entity]:void 0,u=l&&n.entity.startsWith(`event.`)&&![`unknown`,`unavailable`].includes(l.state)?new Date(l.state).toLocaleString(t,{weekday:`short`,hour:`2-digit`,minute:`2-digit`}):``,d=n?[...new Set([...this._sameDevice(n.entity,`camera`),...U(this.hass,e.area_id,`camera`)])]:[],f=n?[...this._sameDevice(n.entity,`select`),...this._sameDevice(n.entity,`text`)]:[],p=n?.away_message,m=p?.entity?this.hass.states[p.entity]:void 0,h=p?.entity?.startsWith(`select.`)?m?.attributes.options??[]:null,g=(e,t,n,r,i,a=L)=>F`
      <div class="cover-follow">
        <ha-icon icon=${e} style="--mdc-icon-size:20px; flex: none; color: ${t?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
        <div class="dusk-text">
          <div class="dusk-title">${n}</div>
          <div class="alarm-opt-hint">${r}</div>
          ${a}
        </div>
        ${i}
      </div>`,_=`announce_tts`in this.settings?this.settings.announce_tts:this.settings.smoke_tts;return F`
      <div class="section ${this._infoOpen(`doorbell`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`doorbell`,V(`doorbell.section`,t))}
        </div>
        ${this._infoText(`doorbell`)}
        ${this._isOpen(`doorbell`)?F`
          <div class="cover-follow" style="margin-top: 0; padding-top: 0; border-top: none">
            <ha-icon icon="mdi:doorbell-video" style="--mdc-icon-size:20px; flex: none; color: ${n?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
            <div class="dusk-text">
              <div class="dusk-title">${V(`doorbell.entity`,t)}</div>
              <div class="alarm-opt-hint">${n?u?`${V(`doorbell.last`,t)} ${u}`:V(`doorbell.never`,t):V(`doorbell.pick_hint`,t)}</div>
            </div>
            <select class="clock-input" style="max-width: 50%" aria-label=${V(`doorbell.entity`,t)}
              @change=${e=>s(e.target.value)}>
              <option value="" ?selected=${!n}>${V(`doorbell.off`,t)}</option>
              ${c.map(e=>F`<option value=${e} ?selected=${n?.entity===e}>${a(e)}</option>`)}
            </select>
          </div>
          ${n?F`
            ${g(`mdi:cctv`,!!n.camera,V(`doorbell.camera`,t),V(`doorbell.camera_hint`,t),F`
              <select class="clock-input" style="max-width: 50%" aria-label=${V(`doorbell.camera`,t)}
                @change=${e=>o({camera:e.target.value||void 0})}>
                <option value="" ?selected=${!n.camera}>${V(`doorbell.no_camera`,t)}</option>
                ${d.map(e=>F`<option value=${e} ?selected=${n.camera===e}>${a(e)}</option>`)}
              </select>`)}
            <div class="alarm-sub">${V(`doorbell.on_ring`,t)}</div>
            ${g(`mdi:pause-circle-outline`,n.pause_media!==!1,V(`doorbell.pause`,t),V(`doorbell.pause_hint`,t),F`<vr-toggle .checked=${n.pause_media!==!1} @change=${e=>o({pause_media:e.detail.value?void 0:!1})}></vr-toggle>`)}
            ${g(`mdi:account-voice`,!!n.announce,V(`doorbell.announce`,t),V(_?`doorbell.announce_hint`:`doorbell.announce_no_tts`,t),F`<vr-toggle .checked=${!!n.announce} .disabled=${!_&&!n.announce} @change=${e=>o({announce:e.detail.value||void 0})}></vr-toggle>`)}
            ${g(`mdi:bell-ring-outline`,n.notify!==!1,V(`doorbell.notify`,t),V(`doorbell.notify_hint`,t),F`<vr-toggle .checked=${n.notify!==!1} @change=${e=>o({notify:e.detail.value?void 0:!1})}></vr-toggle>`)}
            ${g(`mdi:weather-night`,!!n.quiet,V(`doorbell.quiet`,t),V(`doorbell.quiet_hint`,t),F`<vr-toggle .checked=${!!n.quiet} @change=${e=>o({quiet:e.detail.value?{from:`22:30`,to:`07:00`}:void 0})}></vr-toggle>`,n.quiet?F`<div class="slot-times">
                <input type="time" class="clock-input" .value=${n.quiet.from} aria-label=${V(`doorbell.quiet_from`,t)}
                  @change=${e=>{let t=e.target.value;t&&o({quiet:{...n.quiet,from:t}})}} />
                <span class="slot-until">${V(`slots.until`,t)}</span>
                <input type="time" class="clock-input" .value=${n.quiet.to} aria-label=${V(`doorbell.quiet_to`,t)}
                  @change=${e=>{let t=e.target.value;t&&o({quiet:{...n.quiet,to:t}})}} />
              </div>`:L)}
            <div class="alarm-sub">${V(`doorbell.screen`,t)}</div>
            ${f.length===0&&!p?F`<p class="empty-hint" style="padding: 0">${V(`doorbell.screen_none`,t)}</p>`:g(`mdi:message-text-outline`,!!p?.value,V(`doorbell.away_message`,t),V(`doorbell.away_message_hint`,t),F`<vr-toggle .checked=${!!p} @change=${e=>o({away_message:e.detail.value?{entity:f[0]??``,value:``}:void 0})}></vr-toggle>`,p?F`<div class="slot-times">
                    ${f.length>1?F`<select class="clock-input" aria-label=${V(`doorbell.screen`,t)}
                      @change=${e=>o({away_message:{entity:e.target.value,value:``}})}>
                      ${f.map(e=>F`<option value=${e} ?selected=${p.entity===e}>${a(e)}</option>`)}
                    </select>`:L}
                    ${h?F`<select class="clock-input" style="flex: 1 1 auto; min-width: 0" aria-label=${V(`doorbell.away_message`,t)}
                          @change=${e=>o({away_message:{...p,value:e.target.value}})}>
                          <option value="" ?selected=${!p.value}>${V(`doorbell.pick_message`,t)}</option>
                          ${h.map(e=>F`<option value=${e} ?selected=${p.value===e}>${e}</option>`)}
                        </select>`:F`<input class="clock-input" style="flex: 1 1 auto; width: 0; min-width: 0" maxlength="30" .value=${p.value}
                          placeholder=${V(`doorbell.message_placeholder`,t)} aria-label=${V(`doorbell.away_message`,t)}
                          @change=${e=>o({away_message:{...p,value:e.target.value}})} />`}
                  </div>`:L)}
          `:L}
        `:this._foldItems(`doorbell`,n?[{icon:`mdi:doorbell-video`,title:a(n.entity),pills:[u?`${V(`doorbell.last`,t)} ${u}`:``,n.pause_media===!1?``:V(`doorbell.pause`,t),n.announce?V(`doorbell.announce`,t):``,n.quiet?`${V(`doorbell.quiet`,t)} ${n.quiet.from}–${n.quiet.to}`:``,n.away_message?.value?V(`doorbell.away_message`,t):``].filter(Boolean)}]:[],V(`doorbell.none`,t))}
      </div>
    `}_renderSmart(e){let t=this.hass.language,n=G(this.hass,e.area_id)?.attributes.smart??{},r=e=>typeof n[e]==`number`?n[e]:0,i=W(e).length>0,a=(e.media_players??[]).length>0,o=t=>{this.hass.callWS({type:`roomcontrol/forget_learned`,area_id:e.area_id,what:t})},s=[{key:`adaptive_grace`,icon:`mdi:timer-sync-outline`,title:`smart.grace`,hint:`smart.grace_hint`,status:r(`grace_extra`)>0?V(`smart.grace_status`,t).replace(`{min}`,K(r(`grace_extra`))):V(`smart.grace_status_none`,t),forget:r(`grace_extra`)>0?`grace_extra`:void 0,disabled:i?void 0:V(`smart.needs_motion`,t)},{key:`media_hold`,icon:`mdi:television-play`,title:`smart.media`,hint:`smart.media_hint`,status:n.media_active?V(`smart.media_status`,t):void 0,disabled:a?void 0:V(`smart.needs_media`,t)},{key:`last_motion_hold`,icon:`mdi:account-clock-outline`,title:`smart.last_motion`,hint:`smart.last_motion_hint`,status:r(`last_motion_hold`)>0?V(`smart.last_motion_status`,t).replace(`{min}`,String(Math.ceil(r(`last_motion_hold`)/60))):void 0,disabled:i?void 0:V(`smart.needs_motion`,t)},{key:`learn_brightness`,icon:`mdi:brightness-auto`,title:`smart.brightness`,hint:`smart.brightness_hint`,status:e.learn_brightness?V(`smart.brightness_status`,t).replace(`{n}`,String(r(`learned_brightness`))):void 0,forget:r(`learned_brightness`)>0?`brightness`:void 0},{key:`away_replay`,icon:`mdi:home-lightbulb-outline`,title:`smart.replay`,hint:`smart.replay_hint`,status:e.away_replay?n.replay_active?V(`smart.replay_status_active`,t):V(`smart.replay_status`,t).replace(`{n}`,String(r(`replay_days`))):void 0},{key:`anomaly_alerts`,icon:`mdi:bell-alert-outline`,title:`smart.anomaly`,hint:`smart.anomaly_hint`,status:e.anomaly_alerts?V(r(`motion_weeks`)>=2?`smart.anomaly_status_ready`:`smart.anomaly_status_learning`,t).replace(`{weeks}`,String(r(`motion_weeks`))):void 0,disabled:i?void 0:V(`smart.needs_motion`,t)}],c=this._fullSections.has(`smart`),l=c?s:s.filter(t=>e[t.key]===!0);return F`
      <div class="section ${this._infoOpen(`smart`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`smart`,V(`smart.section`,t))}
          ${this._shown(`smart`)?F`<button class="add-btn" aria-expanded=${c?`true`:`false`}
            @click=${()=>this._setFull(`smart`,!c)}>
            <ha-icon icon=${c?`mdi:chevron-up`:`mdi:chevron-down`} style="--mdc-icon-size:16px"></ha-icon>
            ${V(c?`smart.show_less`:`smart.show_more`,t)}
          </button>`:L}
        </div>
        ${this._infoText(`smart`)}
        ${this._isOpen(`smart`)?F`
          ${l.length===0?F`<p class="empty-hint" style="padding: 0">${V(`smart.fold_none`,t)}</p>`:L}
          ${l.map((n,r)=>{let i=e[n.key]===!0;return F`
              <div class="cover-follow" style=${r===0?`margin-top: 0; padding-top: 0; border-top: none`:``}>
                <ha-icon icon=${n.icon} style="--mdc-icon-size:20px; flex: none; color: ${i?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
                <div class="dusk-text">
                  <div class="dusk-title">${V(n.title,t)}</div>
                  <div class="alarm-opt-hint">${V(n.hint,t)}</div>
                  ${n.disabled&&!i?F`<div class="alarm-opt-hint">${n.disabled}</div>`:L}
                  ${i&&n.status?F`<div class="alarm-opt-hint" style="color: var(--primary-color)">${n.status}${n.forget?F` · <button class="link-btn" @click=${()=>o(n.forget)}>${V(`smart.forget`,t)}</button>`:L}</div>`:L}
                </div>
                <vr-toggle .checked=${i} .disabled=${!!n.disabled&&!i}
                  @change=${e=>this._patch({[n.key]:e.detail.value?!0:void 0})}></vr-toggle>
              </div>`})}
        `:L}
      </div>
    `}_vacuumStateText(e){let t=this.hass.language,n=this.hass.states[e];if(!n)return`—`;let r=[`cleaning`,`docked`,`idle`,`paused`,`returning`,`error`,`unavailable`].includes(n.state)?V(`vacuum.state_${n.state}`,t):n.state,i=n.attributes.battery_level;return typeof i==`number`?`${r} · ${i}%`:r}static _vacuumedToday(e){if(!e)return!1;let t=new Date(e),n=new Date;return t.getFullYear()===n.getFullYear()&&t.getMonth()===n.getMonth()&&t.getDate()===n.getDate()}async _vacuumNow(e){this._vacuumBusy=!0,this._vacuumError=``;try{await this._flushSave(),await this.hass.callWS({type:`roomcontrol/vacuum_start`,area_id:e})}catch{this._vacuumError=V(`vacuum.start_failed`,this.hass.language)}finally{this._vacuumBusy=!1}}_addPlan(e){let t=e.vacuum_plans??[],n=``;do n=`v${Date.now().toString(36)}${Math.random().toString(36).slice(2,5)}`;while(t.some(e=>e.id===n));let r={id:n,name:``,enabled:!0,time:`10:00`,days:[0,1,2,3,4],home_persons:[],alarm_states:[],retry:!0,retry_until:`18:00`};this._patch({vacuum_plans:[...t,r]}),this._openPlans=new Set([...this._openPlans,n])}_vacuumPersons(){let e=this.settings.vacuum_persons??this.enabledPersons;return this.enabledPersons.filter(t=>e.includes(t))}_planHome(e){return e.home_persons??[]}_setPlan(e,t){let n=this._draft?.vacuum_plans??[];this._patch({vacuum_plans:n.map(n=>n.id===e?{...n,...t}:n)})}_renderVacuum(e){let t=this.hass.language,n=e.vacuums??[],r=U(this.hass,e.area_id,`vacuum`);if(n.length===0&&r.length===0)return L;let i=r.length?r:Object.keys(this.hass.states).filter(e=>e.startsWith(`vacuum.`)).sort(),a=n[0],o=e.vacuum_plans??[],s=e.vacuum_enabled!==!1,c=G(this.hass,e.area_id),l=c?.attributes.vacuumed_at,u=X._vacuumedToday(l),d=c?.attributes.vacuum_plans??{},f=[0,1,2,3,4,5,6].map(e=>V(`clock.day_${e}`,t)),p=e=>new Date(e).toLocaleString(t,{weekday:`short`,hour:`2-digit`,minute:`2-digit`}),m=a?`${this._vacuumStateText(a)} · ${V(u?`vacuum.done_today`:`vacuum.not_today`,t)}`+(o.length?` · ${V(`vacuum.fold_plans`,t).replace(`{n}`,String(o.length))}`:``)+(o.length&&!s?` (${V(`vacuum.fold_off`,t)})`:``):V(`vacuum.none`,t);return F`
      <div class="section ${this._infoOpen(`vacuum`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`vacuum`,V(`vacuum.section`,t))}
          ${this._isOpen(`vacuum`)&&a?F`<button class="add-btn" @click=${()=>this._addPlan(e)}>
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>${V(`vacuum.add_plan`,t)}
          </button>`:!this._isOpen(`vacuum`)&&a?F`
            <ha-icon icon="mdi:robot-vacuum" class="vacuum-done ${u?`today`:``}"
              title=${V(u?`vacuum.done_today`:`vacuum.not_today`,t)}></ha-icon>`:L}
        </div>
        ${this._infoText(`vacuum`)}
        ${this._isOpen(`vacuum`)?F`
          ${a?F`
              <div class="light-list">
                <div class="light-row">
                  <ha-icon icon="mdi:robot-vacuum" class="vacuum-done ${u?`today`:``}"></ha-icon>
                  <span class="light-entity" title=${a}>
                    ${this.hass.states[a]?.attributes.friendly_name??a}
                    <span class="vacuum-sub">${l?`${V(u?`vacuum.done_today`:`vacuum.last`,t)} ${p(l)}`:V(`vacuum.never`,t)}</span>
                  </span>
                  <span class="light-state ${this.hass.states[a]?.state===`cleaning`?`active`:``}">${this._vacuumStateText(a)}</span>
                  <button class="chooser-btn" ?disabled=${this._vacuumBusy} @click=${()=>this._vacuumNow(e.area_id)}>
                    <ha-icon icon="mdi:play"></ha-icon>${V(`vacuum.now`,t)}
                  </button>
                  <ha-icon-button
                    class="remove-btn"
                    .label=${V(`common.remove`,t)}
                    .path=${`M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z`}
                    @click=${()=>this._patch({vacuums:[]})}
                  ></ha-icon-button>
                </div>
              </div>
              ${this._vacuumError?F`<p class="empty-hint" style="color: var(--error-color)">${this._vacuumError}</p>`:L}
              <div class="cover-follow">
                <ha-icon icon="mdi:calendar-clock" style="--mdc-icon-size:20px; flex: none; color: ${s?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
                <div class="dusk-text">
                  <div class="dusk-title">${V(`vacuum.schedule_on`,t)}</div>
                  <div class="alarm-opt-hint">${V(s?`vacuum.schedule_on_hint`:`vacuum.schedule_off_hint`,t)}</div>
                </div>
                <vr-toggle .checked=${s} @change=${e=>this._patch({vacuum_enabled:e.detail.value})}></vr-toggle>
              </div>
              ${o.length===0?F`<p class="empty-hint">${V(`vacuum.no_plans`,t)}</p>`:F`
                <div class="group-list" style="margin-top: var(--vr-space-2)">
                  ${o.map((t,n)=>this._renderPlan(e,t,n,o,f,d[t.id]))}
                </div>`}
              <p class="empty-hint info-text" style="padding: var(--vr-space-2) 0 0">${V(this.settings.alarm_entity?`vacuum.alarm_hint`:`vacuum.alarm_none`,t)}</p>
            `:this._addingVacuum?this._renderMultiChooser({available:i,selected:()=>this._vacuumSelection,icon:()=>`mdi:robot-vacuum`,emptyText:V(`vacuum.none_in_area`,t),onChange:e=>{this._vacuumSelection=e},onCancel:()=>{this._addingVacuum=!1},onConfirm:e=>{this._patch({vacuums:e.slice(0,1)}),this._addingVacuum=!1}}):F`<p class="empty-hint">${V(`vacuum.none`,t)}
                  <button class="link-btn" @click=${()=>{this._vacuumSelection=new Set,this._addingVacuum=!0}}>${V(`vacuum.add`,t)}</button></p>`}
        `:this._foldSummary(`vacuum`,m)}
      </div>
    `}_renderPlan(e,t,n,r,i,a){let o=this.hass.language,s=this._openPlans.has(t.id),c=()=>{let e=new Set(this._openPlans);s?e.delete(t.id):e.add(t.id),this._openPlans=e},l=e=>this._setPlan(t.id,e),u=e=>this.hass.states[e]?.attributes.friendly_name??e,d=this._planHome(t),f=t.alarm_states??[],p=e=>V(`alarm_state.${e}`,o),m=this.enabledPersons.filter(e=>this._vacuumPersons().includes(e)||d.includes(e)),h=[t.days.length===7?V(`clock.every_day`,o):[...t.days].sort().map(e=>i[e]).join(`, `)||V(`clock.no_days`,o),[d.length?V(`vacuum.sub_home`,o).replace(`{names}`,d.map(u).join(`, `)):``,f.length?V(`vacuum.sub_alarm`,o).replace(`{states}`,f.map(e=>p(e)).join(`/`)):``].filter(Boolean).join(` ${V(`vacuum.or`,o)} `),!d.length&&!f.length?V(`vacuum.sub_always`,o):``,(d.length||f.length)&&t.retry?V(`vacuum.sub_retry`,o).replace(`{time}`,t.retry_until||`18:00`):``,a?.waiting_until?V(`vacuum.sub_waiting`,o):``].filter(Boolean).join(` · `),g=F`
      <div class="bundle-row ${s?`open`:``}" @click=${s?L:c}>
        <ha-icon class="bundle-icon ${t.enabled?`on`:``}" icon="mdi:robot-vacuum"></ha-icon>
        <span class="clock-time ${t.enabled?``:`off`}">${t.time}</span>
        <div class="bundle-text">
          <span class="bundle-title">${t.name||V(`vacuum.default_name`,o)}</span>
          <span class="bundle-sub">${h}</span>
        </div>
        ${this._moveCtl({index:n,count:r.length,name:t.name||t.time,onMove:e=>this._patch({vacuum_plans:X._moved(r,n,e)})})}
        <span @click=${e=>e.stopPropagation()}>
          <vr-toggle .checked=${t.enabled} @change=${e=>l({enabled:e.detail.value})}></vr-toggle>
        </span>
        <button class="bundle-expand" aria-expanded=${s?`true`:`false`}
          aria-label=${V(s?`bundles.collapse`:`bundles.expand`,o)}
          @click=${e=>{e.stopPropagation(),c()}}>
          <ha-icon icon=${s?`mdi:chevron-up`:`mdi:chevron-down`}></ha-icon>
        </button>
      </div>`;return s?F`
      <div class="bundle-card open">
        ${g}
        <div class="bundle-body">
          <div class="clock-line">
            ${F`<label class="clock-field">${V(`clock.time`,o)}
              <input type="time" class="clock-input" .value=${t.time}
                @change=${e=>{let t=e.target.value;t&&l({time:t})}} />
            </label>`}
            <label class="clock-field" style="flex: 1">${V(`clock.name`,o)}
              <input class="clock-input" style="width: 100%" .value=${t.name} placeholder=${V(`vacuum.default_name`,o)}
                @input=${e=>l({name:e.target.value})} />
            </label>
          </div>

          <div class="alarm-sub">${V(`vacuum.home_persons`,o)}</div>
          ${m.length===0?F`<p class="empty-hint" style="padding: 0">${V(`vacuum.persons_none`,o)}</p>`:F`<div class="chip-row">
                ${m.map(e=>F`
                  <button class="chip chip-toggle ${d.includes(e)?`on`:``}" role="checkbox"
                    aria-checked=${d.includes(e)?`true`:`false`}
                    @click=${()=>l({home_persons:d.includes(e)?d.filter(t=>t!==e):[...d,e]})}>
                    <ha-icon icon=${d.includes(e)?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
                    ${u(e)}
                  </button>`)}
              </div>
              <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">${V(d.length?`vacuum.home_chosen`:`vacuum.home_anyone`,o)}</p>`}

          <div class="alarm-sub">${V(`vacuum.alarm_states`,o)}</div>
          <div class="chip-row">
            ${[`disarmed`,`armed_home`,`armed_away`].map(e=>F`
              <button class="chip chip-toggle ${f.includes(e)?`on`:``}" role="checkbox"
                aria-checked=${f.includes(e)?`true`:`false`}
                @click=${()=>l({alarm_states:f.includes(e)?f.filter(t=>t!==e):[...f,e]})}>
                <ha-icon icon=${f.includes(e)?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
                ${p(e)}
              </button>`)}
          </div>
          <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">${this.settings.alarm_entity?V(f.length?`vacuum.alarm_states_chosen`:`vacuum.alarm_states_any`,o):V(`vacuum.alarm_states_no_panel`,o)}</p>

          ${F`
            <div class="alarm-sub">${V(`clock.days`,o)}</div>
            <div class="chip-row">
              ${i.map((e,n)=>F`
                <button class="chip chip-day ${t.days.includes(n)?`on`:``}" role="checkbox"
                  aria-checked=${t.days.includes(n)?`true`:`false`}
                  @click=${()=>l({days:t.days.includes(n)?t.days.filter(e=>e!==n):[...t.days,n].sort()})}>
                  ${e}</button>`)}
            </div>`}

          ${d.length||f.length?F`
            <div class="cover-follow">
              <ha-icon icon="mdi:timer-sand" style="--mdc-icon-size:20px; flex: none; color: ${t.retry?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
              <div class="dusk-text">
                <div class="dusk-title">${V(`vacuum.retry`,o)}</div>
                <div class="alarm-opt-hint">${V(t.retry?`vacuum.retry_on`:`vacuum.retry_off`,o).replace(`{time}`,t.retry_until||`18:00`)}</div>
              </div>
              <vr-toggle .checked=${!!t.retry} @change=${e=>l({retry:e.detail.value})}></vr-toggle>
            </div>
            ${t.retry?F`<div class="clock-line" style="margin-top: var(--vr-space-2)">
              <label class="clock-field">${V(`vacuum.retry_until`,o)}
                <input type="time" class="clock-input" .value=${t.retry_until||`18:00`}
                  @change=${e=>{let t=e.target.value;t&&l({retry_until:t})}} />
              </label>
            </div>`:L}`:L}

          <div class="alarm-summary">
            ${a?.next?F`${V(`vacuum.next`,o)} ${new Date(a.next).toLocaleString(o,{weekday:`short`,hour:`2-digit`,minute:`2-digit`})}. `:L}
            ${a?.waiting_until?F`${V(`vacuum.waiting`,o).replace(`{time}`,new Date(a.waiting_until).toLocaleTimeString(o,{hour:`2-digit`,minute:`2-digit`}))} `:L}
            <button class="link-btn" @click=${()=>this._patch({vacuum_plans:r.filter(e=>e.id!==t.id)})}>${V(`vacuum.delete_plan`,o)}</button>
          </div>
        </div>
      </div>
    `:F`<div class="bundle-card">${g}</div>`}_renderDoors(e){let t=this.hass.language,n=e.door_sensors??[];if(n.length===0&&U(this.hass,e.area_id,`binary_sensor`,[`door`,`garage_door`,`opening`]).length===0)return L;e.groups,e.door_groups;let r=e=>[`on`,`open`].includes(this.hass.states[e]?.state??``);return F`
      <div class="section ${this._infoOpen(`doors`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`doors`,V(`door.section`,t))}
          ${this._shown(`doors`)?F`<button class="add-btn" @click=${()=>{this._setFull(`doors`,!0),this._doorSelection=new Set,this._addingDoor=!0}}>
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>
            ${V(`room.sensor_add`,t)}
          </button>`:L}
        </div>
        ${this._infoText(`doors`)}
        ${this._isOpen(`doors`)?F`

        ${n.length===0?this._addingDoor?L:F`<p class="empty-hint">${V(`door.none`,t)}</p>`:F`<div class="light-list">
              ${n.map((e,i)=>this._renderSensorRow(e,r(e)?`mdi:door-open`:`mdi:door-closed`,r(e)?`var(--vr-on)`:`var(--secondary-text-color)`,r(e)?V(`door.open`,t):V(`door.closed`,t),r(e),()=>this._setDoors(n.filter(t=>t!==e)),this._mover(n,i,e=>this._setDoors(e))))}
            </div>`}

        ${this._addingDoor?this._renderMultiChooser({available:U(this.hass,e.area_id,`binary_sensor`,[`door`,`garage_door`,`opening`]).filter(e=>!n.includes(e)),selected:()=>this._doorSelection,icon:()=>`mdi:door`,emptyText:V(`door.none_in_area`,t),onChange:e=>{this._doorSelection=e},onCancel:()=>{this._addingDoor=!1},onConfirm:e=>{this._setDoors([...n,...e]),this._addingDoor=!1}}):L}

        ${n.length>0?F`<p class="empty-hint info-text" style="padding-bottom: 0">${V(`door.per_bundle`,t)}</p>`:L}
        `:this._foldItems(`doors`,n.map(e=>{let n=this.hass.states[e],i=r(e),a=this._battery(e);return{icon:i?`mdi:door-open`:`mdi:door-closed`,title:this._entName(e),pills:[n?.last_changed?`${V(`fold.since`,t)} ${this._when(n.last_changed)}`:``,a?`${V(`fold.battery`,t)} ${a.text}`:``].filter(Boolean),status:V(i?`door.open`:`door.closed`,t),tone:i||a?.low?`warn`:``}}),V(`door.none_hint`,t))}
      </div>
    `}_setDoors(e){this._patch({door_sensors:[...new Set(e)]})}_patch(e){this._draft&&={...this._draft,...e}}_renderBundles(e){let t=this.hass.language,n=e.groups??[],r=new Set(e.lights.map(e=>e.entity_id)),i=U(this.hass,e.area_id,`light`).filter(e=>!r.has(e)),a=e=>this.hass.states[e]?.attributes.friendly_name??e;return F`
      <div class="section ${this._infoOpen(`lights`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`lights`,V(`room.lights_section`,t))}
          ${this._isOpen(`lights`)&&this._bundleAdd===null?F`
            <button class="add-btn" @click=${()=>{this._bundleSel=new Set,this._bundleAdd=`new`}}>
              <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>
              ${V(`bundles.add`,t)}
            </button>
          `:L}
        </div>
        ${this._infoText(`lights`)}
        ${this._isOpen(`lights`)?F`
        ${n.length>0?this._renderHaName(e,`lights_name`,``,`mdi:lightbulb-group`):L}

        ${n.length===0&&this._bundleAdd===null?F`<p class="empty-hint">${V(`bundles.none`,t)}</p>`:L}

        ${this._bundleAdd===`new`?F`<div class="chooser-caption" style="margin-top: var(--vr-space-2)">${V(`bundles.pick`,t)}</div>
            ${this._renderMultiChooser({available:i,selected:()=>this._bundleSel,icon:e=>this.hass.states[e]?.state===`on`?`mdi:lightbulb`:`mdi:lightbulb-outline`,emptyText:V(`bundles.no_free`,t),onChange:e=>{this._bundleSel=e},onCancel:()=>{this._bundleAdd=null},onConfirm:e=>{if(!this._draft)return;let r=e.length===1?a(e[0]):`${V(`bundles.default_name`,t)} ${n.length+1}`,i=new Set((this._draft.groups??[]).map(e=>e.id));this._draft=Pt(this._draft,e,r);let o=(this._draft.groups??[]).find(e=>!i.has(e.id));o&&(this._openBundles=new Set([...this._openBundles,o.id])),this._bundleAdd=null}})}`:L}

        ${(()=>{let r=n.filter(t=>{let n=Bt(e,t);return n.follow_schedule&&!n.own_times});return(e.schedules??[]).length?F`<div class="convert-card">
            <ha-icon icon="mdi:calendar-sync"></ha-icon>
            <div class="dusk-text">
              <div class="dusk-title">${V(`bundles.convert_title`,t)}</div>
              <div class="alarm-opt-hint">${r.length?V(`bundles.convert_hint`,t).replace(`{names}`,r.map(e=>e.name||``).filter(Boolean).join(`, `)):V(`bundles.convert_unused`,t)}</div>
              ${this._convertError?F`<div class="alarm-opt-hint" style="color: var(--error-color)">${this._convertError}</div>`:L}
            </div>
            <button class="chooser-btn" ?disabled=${this._converting} @click=${()=>this._convertScheduleBundles(e)}>
              <ha-icon icon=${r.length?`mdi:swap-horizontal`:`mdi:link-off`}></ha-icon>${V(r.length?`bundles.convert_btn`:`bundles.unlink_btn`,t)}
            </button>
          </div>`:L})()}

        <div class="group-list" style="margin-top: var(--vr-space-2)">
          ${n.map((t,n)=>this._renderBundle(e,t,n,i))}
        </div>
        `:this._foldSummary(`lights`,n.length===0?V(`bundles.none_short`,t):V(`fold.lights`,t).replace(`{n}`,String(n.length)).replace(`{on}`,String(n.filter(e=>kt(this.hass,e).any_on).length)))}
      </div>
    `}async _convertScheduleBundles(e){let t=this.hass.language;this._converting=!0,this._convertError=``;try{let n=this._draft??e;if(!(n.groups??[]).some(e=>{let t=Bt(n,e);return t.follow_schedule&&!t.own_times})){this._draft={...n,schedules:[],schedule_selector:``};return}let r=G(this.hass,e.area_id)?.attributes.active_schedule||(e.schedules??[])[0],i=await this.hass.callWS({type:`schedule/list`}),a=this.hass.states[r]?.attributes.friendly_name,o=i.find(e=>`schedule.${e.id}`===r)??i.find(e=>e.name===a);if(!o)throw Error(V(`bundles.convert_not_found`,t));let s=[`monday`,`tuesday`,`wednesday`,`thursday`,`friday`,`saturday`,`sunday`],c=new Map;s.forEach((e,t)=>{for(let n of o[e]??[]){let e=`${n.from.slice(0,5)}|${n.to.slice(0,5).replace(`24:00`,`00:00`)}`;c.set(e,[...c.get(e)??[],t])}});let l=e=>[...c.entries()].map(([t,n])=>{let[r,i]=t.split(`|`);return{days:n,start:e===`dusk`||e===`dark`?{type:e}:{type:`time`,time:r},end:{type:`time`,time:i}}}),u=this._draft??e;for(let e of u.groups??[]){let t=Bt(u,e);t.follow_schedule&&!t.own_times&&(u=Lt(u,e.id,{own_times:!0,follow_schedule:!1,slots:l(t.on_from??`schedule`)}))}this._draft={...u,schedules:[],schedule_selector:``}}catch(e){this._convertError=e?.message||V(`bundles.convert_failed`,t)}finally{this._converting=!1}}_slotSummary(e){let t=this.hass.language,n=[0,1,2,3,4,5,6].map(e=>V(`clock.day_${e}`,t));return[e.days.length===7?V(`clock.every_day`,t):[...e.days].sort().map(e=>n[e]).join(`, `)||V(`clock.no_days`,t),`${e.start.type===`time`?e.start.time:V(`slots.start_${e.start.type}`,t)}–${e.end.type===`time`?e.end.time:V(`slots.end_sunrise`,t)}`,e.dim_at?`${V(`slots.dim`,t).toLowerCase()} ${e.dim_at}`:``,e.holiday===`vacation`?V(`slots.holiday_vacation`,t).toLowerCase():``].filter(Boolean).join(` · `)}_renderSlots(e,t,n,r=``){let i=this.hass.language,a=[0,1,2,3,4,5,6].map(e=>V(`clock.day_${e}`,i)),o=(n,r)=>t(e.map((e,t)=>t===n?{...e,...r}:e)),s=e.some(e=>e.start.type===`dusk`),c=Object.keys(this.hass.states).find(e=>e.startsWith(`switch.`)&&this.hass.states[e].attributes.roomcontrol_vacation===!0),l=c?this.hass.states[c].state===`on`:!1;return F`
      <div class="alarm-sub">${V(`slots.title`,i)}${c?F` <span class="alarm-tab-now">· ${V(l?`slots.vacation_on`:`slots.vacation_off`,i)}</span>`:L}</div>
      ${e.length===0?F`<p class="empty-hint" style="padding: 0">${V(`slots.none`,i)}</p>`:L}
      <div class="slot-list">
        ${e.map((n,s)=>F`
          ${this._openSlots.has(`${r}:${s}`)?F`
          <div class="slot-row">
            <div class="slot-head">
            <input class="clock-input slot-name" .value=${n.name??``}
              placeholder="${V(`slots.name_placeholder`,i)} ${s+1}"
              aria-label=${V(`slots.name`,i)}
              @input=${e=>o(s,{name:e.target.value})} />
              <button class="bundle-expand" aria-expanded="true" aria-label=${V(`bundles.collapse`,i)}
                @click=${()=>{let e=new Set(this._openSlots);e.delete(`${r}:${s}`),this._openSlots=e}}>
                <ha-icon icon="mdi:chevron-up"></ha-icon>
              </button>
            </div>
            <div class="slot-days-row">
              <div class="chip-row slot-days">
                ${a.map((e,t)=>F`
                  <button class="chip chip-day ${n.days.includes(t)?`on`:``}" role="checkbox"
                    aria-checked=${n.days.includes(t)?`true`:`false`}
                    @click=${()=>o(s,{days:n.days.includes(t)?n.days.filter(e=>e!==t):[...n.days,t].sort()})}>
                    ${e}</button>`)}
              </div>

            </div>
            <div class="slot-times">
              <select class="clock-input" aria-label=${V(`slots.start`,i)}
                @change=${e=>{let t=e.target.value;o(s,{start:t===`time`?{type:`time`,time:`18:00`}:{type:t}})}}>
                ${[`time`,`dusk`,`dark`].map(e=>F`<option value=${e} ?selected=${n.start.type===e}>${V(`slots.start_${e}`,i)}</option>`)}
              </select>
              ${n.start.type===`time`?F`<input type="time" class="clock-input" .value=${n.start.time}
                aria-label=${V(`slots.start`,i)}
                @change=${e=>{let t=e.target.value;t&&o(s,{start:{type:`time`,time:t}})}} />`:L}
              <span class="slot-until">${V(`slots.until`,i)}</span>
              <select class="clock-input" aria-label=${V(`slots.end`,i)}
                @change=${e=>{let t=e.target.value;o(s,{end:t===`time`?{type:`time`,time:`23:00`}:{type:`sunrise`}})}}>
                ${[`time`,`sunrise`].map(e=>F`<option value=${e} ?selected=${n.end.type===e}>${V(`slots.end_${e}`,i)}</option>`)}
              </select>
              ${n.end.type===`time`?F`<input type="time" class="clock-input" .value=${n.end.time}
                aria-label=${V(`slots.end`,i)}
                @change=${e=>{let t=e.target.value;t&&o(s,{end:{type:`time`,time:t}})}} />`:L}
              <span style="flex: 1"></span>
              <select class="clock-input" aria-label=${V(`slots.holiday`,i)}
                @change=${e=>o(s,{holiday:e.target.value})}>
                ${[`normal`,`vacation`].map(e=>F`<option value=${e} ?selected=${(n.holiday===`vacation`||n.holiday===`only`?`vacation`:`normal`)===e}>${V(`slots.holiday_${e}`,i)}</option>`)}
              </select>
              <ha-icon-button
                class="remove-btn"
                .label=${V(`common.remove`,i)}
                .path=${`M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z`}
                @click=${()=>t(e.filter((e,t)=>t!==s))}
              ></ha-icon-button>
            </div>
            <div class="slot-times slot-dim-row">
              <ha-icon icon="mdi:brightness-4" style=${n.dim_at?`color: var(--primary-color)`:``}></ha-icon>
              <span class="slot-until">${V(`slots.dim`,i)}</span>
              <vr-toggle .checked=${!!n.dim_at}
                @change=${e=>{if(!e.detail.value){o(s,{dim_at:void 0});return}let t=n.end.type===`time`?n.end.time.split(`:`).map(Number):null,r=t?((t[0]*60+t[1]-30)%1440+1440)%1440:1320;o(s,{dim_at:`${String(Math.floor(r/60)).padStart(2,`0`)}:${String(r%60).padStart(2,`0`)}`})}}></vr-toggle>
              ${n.dim_at?F`
                <span class="slot-until">${V(`slots.dim_at`,i)}</span>
                <input type="time" class="clock-input" .value=${n.dim_at}
                  aria-label=${V(`slots.dim_at`,i)}
                  @change=${e=>{let t=e.target.value;t&&o(s,{dim_at:t})}} />`:L}
            </div>
          </div>`:F`
          <button class="slot-row slot-folded" aria-expanded="false"
            @click=${()=>{this._openSlots=new Set([...this._openSlots,`${r}:${s}`])}}>
            <ha-icon icon=${n.holiday===`vacation`?`mdi:palm-tree`:`mdi:clock-outline`}></ha-icon>
            <span class="slot-folded-text">
              <span class="slot-folded-name">${n.name||`${V(`slots.name_placeholder`,i)} ${s+1}`}</span>
              <span class="slot-folded-sub">${this._slotSummary(n)}</span>
            </span>
            <ha-icon icon="mdi:chevron-down"></ha-icon>
          </button>`}`)}
      </div>
      <button class="add-btn" style="margin-top: var(--vr-space-2)"
        @click=${()=>{this._openSlots=new Set([...this._openSlots,`${r}:${e.length}`]),t([...e,{days:[0,1,2,3,4,5,6],start:{type:`time`,time:`18:00`},end:{type:`time`,time:`23:00`}}])}}>
        <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>${V(`slots.add`,i)}
      </button>
      <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`slots.hint`,i)} ${V(`slots.holiday_hint`,i)}${s?` ${V(n?`slots.dusk_lux`:`slots.dusk_ramp`,i)}`:``}</p>
    `}_renderBundle(e,t,n,r){let i=this.hass.language,a=Bt(e,t),o=kt(this.hass,t),s=`${V(`bundles.default_name`,i)} ${n+1}`,c=t.name||s,l=(e.groups??[]).length,u=e=>this.hass.states[e]?.attributes.friendly_name??e,d=e=>{this._draft&&=Lt(this._draft,t.id,e)},f=ft(this.hass,e.sun_entity||`sun.sun`,a.daylight_min_kelvin,a.daylight_max_kelvin),p=e=>{let[t,n,r]=pt(e);return F`<span class="swatch" style="background: rgb(${t}, ${n}, ${r})"></span>`},m=W(e).length>0,h=(e.door_sensors??[]).length>0,g=at(e).length>0,_=e.target_lux_enabled===!1,v=this._openBundles.has(t.id),y=()=>{let e=new Set(this._openBundles);v?e.delete(t.id):e.add(t.id),this._openBundles=e},b=o.avg_brightness===null?null:Math.round((o.avg_brightness??255)/255*100),x=[{key:`on_motion`,icon:`mdi:motion-sensor`,label:V(`bundles.t_motion`,i),ok:m,why:V(`bundles.no_motion_sensor`,i)},{key:`on_door`,icon:`mdi:door-open`,label:V(`bundles.t_door`,i),ok:h,why:V(`bundles.no_door_sensor`,i)},{key:`own_times`,icon:`mdi:clock-outline`,label:V(`bundles.t_own_times`,i),ok:!0,why:``}],S=x.filter(e=>a[e.key]&&e.ok).map(e=>e.label.toLowerCase()),C=a.brightness_mode===`fixed`?V(`bundles.sub_fixed`,i).replace(`{pct}`,String(a.brightness||50)):a.brightness>0?V(`bundles.sub_max`,i).replace(`{pct}`,String(a.brightness)):V(`bundles.sub_default`,i),ee=[V(t.lights.length===1?`bundles.one_lamp`:`bundles.n_lamps`,i).replace(`{n}`,String(t.lights.length)),S.length?S.join(`, `):V(`bundles.sub_by_hand`,i),a.follow_daylight?V(`bundles.sub_daylight`,i):C].join(` · `),w=o.any_on?`${V(`card.on`,i)}${b===null?``:` · ${b}%`}`:V(`card.off`,i),T=G(this.hass,this.room.area_id)?.attributes.hand_set??[],te=t.lights.filter(e=>T.includes(e)),E=F`
      <div class="bundle-row ${v?`open`:``}" @click=${v?L:y}>
        <ha-icon class="bundle-icon ${o.any_on?`on`:``}" icon=${o.any_on?`mdi:lightbulb-group`:`mdi:lightbulb-group-outline`}></ha-icon>
        <div class="bundle-text">
          ${v?F`<input class="group-name" .value=${t.name} placeholder=${s}
                aria-label=${V(`groups.name`,i)}
                @click=${e=>e.stopPropagation()}
                @input=${e=>d({name:e.target.value})} />`:F`<span class="bundle-title">${c}</span>`}
          <span class="bundle-sub">${ee}</span>
        </div>
        <span class="alarm-pill ${o.any_on?`lit`:``}">${w}</span>
        ${te.length>0?F`
          <button class="move-btn" title=${V(`bundles.restore`,i)}
            aria-label="${V(`bundles.restore`,i)}: ${c}"
            @click=${e=>{e.stopPropagation(),this.hass.callWS({type:`roomcontrol/restore_auto`,area_id:this.room.area_id,lamps:te})}}>
            <ha-icon icon="mdi:restore"></ha-icon></button>`:L}
        ${l>1?F`<span class="bundle-move" @click=${e=>e.stopPropagation()}>
          <button class="move-btn" ?disabled=${n===0}
            aria-label="${V(`bundles.move_up`,i)}: ${c}" title=${V(`bundles.move_up`,i)}
            @click=${()=>{this._draft&&=zt(this._draft,t.id,-1)}}>
            <ha-icon icon="mdi:chevron-up"></ha-icon></button>
          <button class="move-btn" ?disabled=${n===l-1}
            aria-label="${V(`bundles.move_down`,i)}: ${c}" title=${V(`bundles.move_down`,i)}
            @click=${()=>{this._draft&&=zt(this._draft,t.id,1)}}>
            <ha-icon icon="mdi:chevron-down"></ha-icon></button>
        </span>`:L}
        <button class="bundle-expand" aria-expanded=${v?`true`:`false`}
          aria-label=${V(v?`bundles.collapse`:`bundles.expand`,i)}
          @click=${e=>{e.stopPropagation(),y()}}>
          <ha-icon icon=${v?`mdi:chevron-up`:`mdi:chevron-down`}></ha-icon>
        </button>
      </div>`;if(!v)return F`<div class="bundle-card">${E}</div>`;let D=[V(`bundles.sum_when`,i).replace(`{name}`,c).replace(`{when}`,S.length?S.join(`, `):V(`bundles.sub_by_hand`,i)),a.brightness_mode===`fixed`?V(`bundles.sum_fixed`,i).replace(`{pct}`,String(a.brightness||50)):V(`bundles.sum_default`,i),a.follow_daylight?V(`bundles.sum_daylight`,i):V(`bundles.sum_own_colour`,i),a.dim?V(`bundles.sum_dim`,i):``,a.lux_control&&g&&!_?V(`bundles.sum_lux`,i):``].filter(Boolean).join(` `);return F`
      <div class="bundle-card open">
        ${E}
        <div class="bundle-body">
          <div class="chip-row">
            ${t.lights.map(e=>F`
              <span class="chip" title=${e}>
                <ha-icon icon=${this.hass.states[e]?.state===`on`?`mdi:lightbulb`:`mdi:lightbulb-outline`}
                  style=${this.hass.states[e]?.state===`on`?`color: var(--vr-on)`:``}></ha-icon>
                ${u(e)}
                <button class="chip-x" aria-label="${V(`common.remove`,i)}: ${u(e)}"
                  @click=${()=>{this._draft&&=It(this._draft,e)}}>
                  <ha-icon icon="mdi:close"></ha-icon>
                </button>
              </span>`)}
            ${this._bundleAdd===t.id?L:F`
              <button class="chip chip-add" @click=${()=>{this._bundleSel=new Set,this._bundleAdd=t.id}}>
                <ha-icon icon="mdi:plus"></ha-icon>${V(`bundles.lamp_chip`,i)}
              </button>`}
          </div>
          ${this._bundleAdd===t.id?this._renderMultiChooser({available:r,selected:()=>this._bundleSel,icon:()=>`mdi:lightbulb-outline`,emptyText:V(`bundles.no_free`,i),onChange:e=>{this._bundleSel=e},onCancel:()=>{this._bundleAdd=null},onConfirm:e=>{this._draft&&=Ft(this._draft,t.id,e),this._bundleAdd=null}}):L}

          ${a.brightness_mode===`fixed`?L:F`
            <div class="brightness-row" style="margin-top: var(--vr-space-2)">
              <ha-icon icon="mdi:brightness-auto"></ha-icon>
              <input type="range" min="1" max="100" step="1"
                aria-label="${V(`bundles.auto_max`,i)}: ${c}"
                .value=${String(a.brightness||100)}
                @input=${e=>d({brightness:Number(e.target.value)})} />
              ${this._num(a.brightness||100,1,100,`%`,`${V(`bundles.auto_max`,i)}: ${c}`,e=>d({brightness:e}))}
            </div>
            <p class="empty-hint" style="padding: 0">
              ${a.brightness>0?F`${V(`bundles.auto_max_hint`,i).replace(`{pct}`,String(a.brightness))}
                    <button class="link-btn" @click=${()=>d({brightness:0})}>${V(`bundles.default_level_clear`,i)}</button>`:V(`bundles.auto_max_none`,i)}
            </p>
          `}

          <div class="alarm-sub">${V(`bundles.when_question`,i)}</div>
          <div class="alarm-options" role="group" aria-label=${V(`bundles.when_question`,i)}>
            ${x.map(e=>F`
              <button class="alarm-opt ${a[e.key]&&e.ok?`selected`:``}" role="checkbox"
                aria-checked=${a[e.key]&&e.ok?`true`:`false`} ?disabled=${!e.ok}
                title=${e.ok?``:e.why}
                @click=${()=>d({[e.key]:!a[e.key],...e.key===`own_times`&&!a.own_times?{follow_schedule:!1}:{},...e.key===`own_times`&&!a.own_times&&!(a.slots??[]).length?{slots:[{days:[0,1,2,3,4,5,6],start:{type:`dusk`},end:{type:`time`,time:`23:00`}}]}:{}})}>
                <ha-icon icon=${e.icon}></ha-icon>
                <span class="alarm-opt-title">${e.label}</span>
                ${e.ok?L:F`<span class="alarm-opt-hint">${e.why}</span>`}
              </button>`)}
          </div>
          <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`bundles.when_info`,i)}</p>

          ${a.own_times?this._renderSlots(a.slots??[],e=>d({slots:e}),g&&!_,t.id):L}



          <div class="alarm-sub">${V(`bundles.brightness`,i)}</div>
          <div class="alarm-options" role="radiogroup" aria-label=${V(`bundles.brightness`,i)}>
            ${[`default`,`fixed`].map(e=>F`
              <button class="alarm-opt ${a.brightness_mode===e?`selected`:``}" role="radio"
                aria-checked=${a.brightness_mode===e?`true`:`false`}
                @click=${()=>d({brightness_mode:e,brightness:e===`fixed`?a.brightness||50:0})}>
                <ha-icon icon=${e===`fixed`?`mdi:pin-outline`:`mdi:lightbulb-outline`}></ha-icon>
                <span class="alarm-opt-title">${V(`bundles.mode_${e}`,i)}</span>
                <span class="alarm-opt-hint">${V(`bundles.mode_${e}_card`,i)}</span>
              </button>`)}
          </div>
          ${a.brightness_mode===`fixed`?F`
            <div class="target-lux-row">
              <input type="range" min="1" max="100" step="5"
                aria-label=${V(`bundles.brightness`,i)} .value=${String(a.brightness||50)}
                @input=${e=>d({brightness:Number(e.target.value)})} />
              ${this._num(a.brightness||50,1,100,`%`,V(`bundles.brightness`,i),e=>d({brightness:e}))}
            </div>`:L}
          <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">
            ${a.brightness_mode===`fixed`?V(`bundles.fixed_hint`,i):V(`bundles.default_hint`,i)}
            ${V(`bundles.evening_hint`,i)}
          </p>

          <div class="alarm-sub">${V(`bundles.colour`,i)}</div>
          <div class="alarm-options" role="radiogroup" aria-label=${V(`bundles.colour`,i)}>
            <button class="alarm-opt ${a.follow_daylight?``:`selected`}" role="radio"
              aria-checked=${a.follow_daylight?`false`:`true`} @click=${()=>d({follow_daylight:!1})}>
              <ha-icon icon="mdi:palette-outline"></ha-icon>
              <span class="alarm-opt-title">${V(`bundles.colour_own`,i)}</span>
              <span class="alarm-opt-hint">${V(`bundles.colour_own_card`,i)}</span>
            </button>
            <button class="alarm-opt ${a.follow_daylight?`selected`:``}" role="radio"
              aria-checked=${a.follow_daylight?`true`:`false`} @click=${()=>d({follow_daylight:!0})}>
              <ha-icon icon="mdi:white-balance-sunny"></ha-icon>
              <span class="alarm-opt-title">${V(`bundles.daylight_on`,i)}</span>
              <span class="alarm-opt-hint">${a.daylight_min_kelvin}–${a.daylight_max_kelvin} K${f===null?``:` · ${V(`room.daylight_now`,i).toLowerCase()} ${f} K`}</span>
            </button>
          </div>
          ${a.follow_daylight?F`
            <div class="chip-row" style="margin-top: var(--vr-space-2)">
              <button class="chip chip-toggle ${a.daylight_prefer_rgb?`on`:``}" role="checkbox"
                aria-checked=${a.daylight_prefer_rgb?`true`:`false`}
                @click=${()=>d({daylight_prefer_rgb:!a.daylight_prefer_rgb})}>
                <ha-icon icon=${a.daylight_prefer_rgb?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
                ${V(`daylight.rgb_title`,i)}
              </button>
            </div>
            <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`daylight.rgb_hint`,i)}</p>
            <div class="target-lux-row">
              <span class="fixed-label">${V(`daylight.warmest`,i)}</span>
              <input type="range" min="1500" max="3500" step="100" aria-label=${V(`daylight.warmest`,i)}
                .value=${String(a.daylight_min_kelvin)}
                @input=${e=>d({daylight_min_kelvin:Number(e.target.value)})} />
              ${this._num(a.daylight_min_kelvin,1500,3500,`K`,V(`daylight.warmest`,i),e=>d({daylight_min_kelvin:e}),p(a.daylight_min_kelvin))}
            </div>
            <div class="target-lux-row">
              <span class="fixed-label">${V(`daylight.coolest`,i)}</span>
              <input type="range" min="3500" max="6500" step="100" aria-label=${V(`daylight.coolest`,i)}
                .value=${String(a.daylight_max_kelvin)}
                @input=${e=>d({daylight_max_kelvin:Number(e.target.value)})} />
              ${this._num(a.daylight_max_kelvin,3500,6500,`K`,V(`daylight.coolest`,i),e=>d({daylight_max_kelvin:e}),p(a.daylight_max_kelvin))}
            </div>
          `:L}

          <div class="alarm-sub">${V(`bundles.extra`,i)}</div>
          <div class="chip-row">
            <button class="chip chip-toggle ${a.dim?`on`:``}" role="checkbox" aria-checked=${a.dim?`true`:`false`}
              @click=${()=>d({dim:!a.dim})}>
              <ha-icon icon=${a.dim?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
              ${V(`bundles.extra_dim`,i)}
            </button>
            <button class="chip chip-toggle ${a.lux_control&&g&&!_?`on`:``}" role="checkbox"
              aria-checked=${a.lux_control&&g&&!_?`true`:`false`}
              ?disabled=${!g||_}
              title=${g?_?V(`bundles.lux_target_off`,i):``:V(`bundles.no_lux_sensor`,i)}
              @click=${()=>d({lux_control:!a.lux_control})}>
              <ha-icon icon=${a.lux_control&&g&&!_?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
              ${V(`bundles.extra_lux`,i)}
            </button>
          </div>
          <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">
            ${g?_?V(`bundles.lux_target_off`,i):F`<span class="info-text">${V(`bundles.dim_hint`,i)} ${V(`bundles.lux_hint`,i).replace(`{target}`,String(e.target_lux||300))}</span>`:V(`bundles.no_lux_sensor`,i)}
          </p>

          <div class="alarm-summary">
            ${D}
            <button class="link-btn danger-link" @click=${()=>{this._draft&&=Rt(this._draft,t.id)}}>
              ${V(`bundles.delete`,i)}
            </button>
          </div>
        </div>
      </div>
    `}_renderGroups(e){let t=this.hass.language,n=e.groups??[],r=e.lights.map(e=>e.entity_id);return F`
      <div class="section">
        <div class="section-header">
          <span class="section-title">${V(`groups.section`,t)}</span>
          ${r.length>0&&this._groupEdit===null?F`
            <button class="add-btn" @click=${()=>this._startGroupEdit(`new`,[],``)}>
              <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>
              ${V(`groups.add`,t)}
            </button>
          `:L}
        </div>

        ${r.length===0?F`<p class="empty-hint">${V(`groups.no_lights`,t)}</p>`:n.length===0&&this._groupEdit===null?F`<p class="empty-hint">${V(`groups.none`,t)}</p>`:L}

        <div class="group-list">
          ${n.map((t,n)=>this._groupEdit===t.id?this._renderGroupEditor(e,t.id):this._renderGroup(e,t,n))}
          ${this._groupEdit===`new`?this._renderGroupEditor(e,`new`):L}
        </div>
      </div>
    `}_renderGroup(e,t,n){let r=this.hass.language,i=kt(this.hass,t),a=e.fixed_levels??{},o=t.lights.filter(e=>!(e in a)),s=Ot(t,n,V(`groups.default_name`,r)),c=e=>this.hass.states[e]?.attributes.friendly_name??e;return F`
      <div class="group-card ${i.any_on?`on`:``}">
        <div class="group-head">
          <ha-icon
            icon=${i.any_on?`mdi:lightbulb-group`:`mdi:lightbulb-group-outline`}
            style="color: ${i.any_on?`var(--vr-on)`:`var(--secondary-text-color)`}"
          ></ha-icon>
          <input
            class="group-name"
            .value=${t.name}
            placeholder=${s}
            aria-label=${V(`groups.name`,r)}
            @input=${e=>this._renameGroup(t.id,e.target.value)}
          />
          <vr-toggle
            .checked=${i.any_on}
            .disabled=${t.lights.length===0}
            .label=${``}
            aria-label="${s}: ${i.any_on?V(`card.on`,r):V(`card.off`,r)}"
            @change=${e=>this._switchGroup(t,e.detail.value)}
          ></vr-toggle>
        </div>

        <div class="group-lamps">
          ${t.lights.length===0?F`<span class="empty-hint" style="padding:0">${V(`groups.empty`,r)}</span>`:t.lights.map(e=>F`<span class="lamp-chip ${this.hass.states[e]?.state===`on`?`on`:``}" title=${e}>
                  ${e in a?F`<ha-icon icon="mdi:pin"></ha-icon>`:L}${c(e)}
                </span>`)}
        </div>

        ${i.any_on&&o.length>0?F`
          <div class="brightness-row" style="margin-top: var(--vr-space-2)">
            <ha-icon icon="mdi:brightness-4"></ha-icon>
            <input
              type="range"
              min="1"
              max="255"
              step="1"
              aria-label="${V(`groups.brightness`,r)}: ${s}"
              .value=${String(i.avg_brightness??255)}
              @change=${e=>He(this.hass,o,Number(e.target.value))}
            />
            ${this._num(i.avg_brightness===null?100:Math.round((i.avg_brightness??255)/255*100),1,100,`%`,`${V(`groups.brightness`,r)}: ${s}`,e=>He(this.hass,o,Math.round(e*255/100)))}
          </div>
        `:L}

        <div class="group-actions">
          <button class="chooser-btn" @click=${()=>this._startGroupEdit(t.id,t.lights,t.name)}>
            ${V(`groups.edit_lamps`,r)}
          </button>
          <button class="chooser-btn danger" @click=${()=>this._deleteGroup(t.id)}>
            ${V(`common.remove`,r)}
          </button>
        </div>
      </div>
    `}_renderGroupEditor(e,t){let n=this.hass.language;return F`
      <div class="group-card editing">
        ${t===`new`?F`
          <input
            class="group-name"
            .value=${this._groupNameDraft}
            placeholder=${`${V(`groups.default_name`,n)} ${(e.groups??[]).length+1}`}
            aria-label=${V(`groups.name`,n)}
            @input=${e=>{this._groupNameDraft=e.target.value}}
          />
        `:F`<div class="chooser-caption">${V(`groups.pick_lamps`,n)}</div>`}
        ${this._renderMultiChooser({available:e.lights.map(e=>e.entity_id),selected:()=>this._groupSelection,icon:e=>this.hass.states[e]?.state===`on`?`mdi:lightbulb`:`mdi:lightbulb-outline`,emptyText:V(`groups.no_lights`,n),onChange:e=>{this._groupSelection=e},onCancel:()=>{this._groupEdit=null},onConfirm:e=>this._saveGroupEdit(t,e)})}
      </div>
    `}_startGroupEdit(e,t,n){this._groupEdit=e,this._groupSelection=new Set(t),this._groupNameDraft=n}_saveGroupEdit(e,t){this._draft&&(this._draft=e===`new`?Ct(this._draft,this._groupNameDraft,t):Tt(this._draft,e,t),this._groupEdit=null)}_renameGroup(e,t){this._draft&&=wt(this._draft,e,t)}_deleteGroup(e){if(!this._draft)return;let t=Et(this._draft,e);this._draft={...t,door_groups:(t.door_groups??[]).filter(t=>t!==e)}}async _switchGroup(e,t){await Ge(this.hass,e.lights,t,this._draft?.fixed_levels??{})}_togglePinned(e){if(!this._draft)return;let t={...this._draft.fixed_levels??{}};e in t?delete t[e]:t[e]=50,this._draft={...this._draft,fixed_levels:t}}_setFixedLevel(e,t){this._draft&&={...this._draft,fixed_levels:{...this._draft.fixed_levels??{},[e]:Math.min(100,Math.max(1,Math.round(t)))}}}_areaName(e){return this.hass.areas?.[e]?.name??this.allRooms.find(t=>t.area_id===e)?.name??e}_addLinks(e){if(!this._draft)return;let t=this._draft.linked_rooms??[];this._draft={...this._draft,linked_rooms:[...t,...e.filter(e=>!t.includes(e))]},this._addingLinks=!1,this._selectedLinks=new Set}_removeLink(e){this._draft&&={...this._draft,linked_rooms:(this._draft.linked_rooms??[]).filter(t=>t!==e)}}_renderManual(e){let t=this.hass.language,n=gt(this.hass,e.area_id),r=e.manual_duration??60;return F`
      <div class="manual-card active">
        <div class="manual-head">
          <ha-icon icon="mdi:hand-back-right-outline"></ha-icon>
          <div class="manual-text">
            <div class="manual-title">${V(`manual.title`,t)}</div>
            <div class="manual-sub" role="status" aria-live="polite">
              ${V(`manual.active`,t)} · ${V(`grace.left`,t)} <strong>${_t(n??0)}</strong>
            </div>
          </div>
          <button class="chooser-btn" @click=${()=>this._toggleManual(!0)}>
            ${V(`manual.stop`,t)}
          </button>
        </div>
        <div class="target-lux-row">
          <ha-icon icon="mdi:timer-cog-outline"></ha-icon>
          <input
            type="range"
            min="5"
            max="480"
            step="5"
            aria-label=${V(`manual.duration`,t)}
            .value=${String(r)}
            @input=${this._onManualDurationInput}
            @change=${this._onManualDurationChange}
          />
          ${this._num(r,5,480,`min`,V(`manual.duration`,t),t=>{this._draft&&={...this._draft,manual_duration:t},ze(this.hass,e.area_id,t)},F`<span class="slider-extra">${vt(r,V(`analysis.hour_short`,t))}</span>`)}
        </div>
      </div>
    `}_onManualDurationInput(e){this._draft&&={...this._draft,manual_duration:Number(e.target.value)}}async _onManualDurationChange(e){this._draft&&await ze(this.hass,this._draft.area_id,Number(e.target.value))}async _toggleManual(e){this._draft&&(await this._flushSave(),await ze(this.hass,this._draft.area_id,e?0:void 0))}_renderMotionDiagnostics(e){let t=this.hass.language,n=G(this.hass,e.area_id);if(!n)return F`<p class="motion-note warn">${V(`motion_note.no_entity`,t)}</p>`;let r=n.attributes.motion_sensors,i=W(e).filter(e=>!(r??[]).includes(e));if(r===void 0||i.length>0&&this._saveState!==`pending`&&this._saveState!==`saving`)return F`<p class="motion-note warn">${V(`motion_note.not_tracked`,t)}</p>`;let a=n.attributes.motion_note;if(!a)return L;let o=V(`motion_note.${a}`,t);if(a===`too_bright`&&at(e).length>0){let t=ct(this.hass,e);o=o.replace(`{lux}`,t===null?`?`:String(Math.round(t))).replace(`{target}`,String(e.dark_lux??e.target_lux??0))}return F`<p class="motion-note">${V(`motion_note.ignored`,t)}: ${o}</p>`}_onGraceInput(e){this._draft&&={...this._draft,motion_off_delay:Number(e.target.value)}}_renderGraceRow(e){let t=ht(this.hass,e.area_id);if(t===null)return L;let n=this.hass.language;return F`<div class="master-row" style="font-size: var(--vr-font-sm);">
      <ha-icon icon="mdi:timer-sand" style="--mdc-icon-size:16px; color: var(--vr-motion)"></ha-icon>
      ${V(`grace.label`,n)} · ${V(`grace.left`,n)} ${K(t)}
    </div>`}_addMotion(e){if(!this._draft)return;let t=W(this._draft);this._draft={...this._draft,motion_sensors:[...t,...e.filter(e=>!t.includes(e))],motion_sensor:``},this._addingMotion=!1,this._selectedMotion=new Set}_removeMotion(e){this._draft&&={...this._draft,motion_sensors:W(this._draft).filter(t=>t!==e),motion_sensor:``}}_setLuxSensors(e){this._draft&&={...this._draft,lux_sensors:e,lux_sensor:e[0]??``}}_renderLuxAlarmPause(e){let t=this.hass.language,n=e.lux_control_off_alarm??[],r=e.alarm_entity||this.settings.alarm_entity||``,i=r?this.hass.states[r]?.state:void 0,a=[`disarmed`,`armed_home`,`armed_away`],o=e=>{let n=`alarm_state.${e}`,r=V(n,t);return r===n?e:r},s=e=>{let t=n.includes(e)?n.filter(t=>t!==e):[...n,e];this._patch({lux_control_off_alarm:t.length?t:void 0})},c=!!i&&n.includes(i);return F`
      <div class="lux-alarm">
        <div class="alarm-opt-title">${V(`lux.alarm_pause_title`,t)}</div>
        <div class="chip-row" role="group" aria-label=${V(`lux.alarm_pause_title`,t)}>
          ${a.map(e=>F`
            <button class="chip chip-toggle ${n.includes(e)?`on`:``}" role="checkbox"
              aria-checked=${n.includes(e)?`true`:`false`} @click=${()=>s(e)}>
              <ha-icon icon=${n.includes(e)?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
              ${o(e)}${i===e?F` <span class="alarm-tab-now">· ${V(`alarm.now`,t).toLowerCase()}</span>`:L}
            </button>`)}
        </div>
        <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">
          ${r?n.length===0?V(`lux.alarm_pause_none`,t):V(`lux.alarm_pause_hint`,t).replace(`{states}`,n.map(o).join(`, `)):V(`lux.alarm_pause_no_panel`,t)}
          ${c?F`<br /><strong>${V(`lux.alarm_paused_now`,t)}</strong>`:L}
        </p>
      </div>
    `}_renderLux(e,t){let n=this.hass.language,r=at(e),i=e=>{let t=this.hass.states[e]?.state;return t!==void 0&&t!==``&&Number.isFinite(Number(t))?Number(t):null},a=r.map(i).filter(e=>e!==null),o=e.lux_mode??`average`,s=e.dark_lux??e.target_lux??0,c=t!==null&&Number.isFinite(t)?Math.round(t):null,l=s<=0||c!==null&&c<s,u=e.target_lux_enabled!==!1,d=e.target_lux||300,f=e=>e===null?`—`:`${Math.round(e)} lx`,p={average:`mdi:approximately-equal`,min:`mdi:arrow-down`,max:`mdi:arrow-up`,median:`mdi:format-align-middle`,sum:`mdi:plus`},m=c===null?``:`${V(`alarm.now`,n)}: ${c} lx · ${V(l?`lux.is_dark`:`lux.is_light`,n)}`,h=r.length===0?V(`room.lux_none`,n):[c===null?``:V(l?`lux.sum_now_dark`:`lux.sum_now_light`,n).replace(`{how}`,r.length>1?V(`lux.mode_${o}`,n).toLowerCase():V(`lux.sum_single`,n)).replace(`{lux}`,String(c)),s>0?V(`lux.sum_dark`,n).replace(`{lux}`,String(s)):V(`lux.sum_always_dark`,n),u?V(`lux.sum_target`,n).replace(`{lux}`,String(d)):V(`lux.sum_target_off`,n),u&&(e.lux_control_off_alarm??[]).length?V(`lux.sum_alarm_pause`,n).replace(`{states}`,(e.lux_control_off_alarm??[]).map(e=>{let t=V(`alarm_state.${e}`,n);return t===`alarm_state.${e}`?e:t}).join(`, `)):``].filter(Boolean).join(` `);return F`
      <div class="section ${this._infoOpen(`lux`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`lux`,V(`room.lux_section`,n))}
          ${m?F`<span class="alarm-pill">${m}</span>`:L}
        </div>
        ${this._infoText(`lux`)}
        ${this._isOpen(`lux`)?F`
        <div class="alarm-card">
          <div class="chip-row">
            ${r.map(e=>F`
              <span class="chip" title=${e}>
                <ha-icon icon="mdi:brightness-5"></ha-icon>
                ${this.hass.states[e]?.attributes.friendly_name??e} · ${f(i(e))}
                <button class="chip-x" aria-label="${V(`common.remove`,n)}: ${this.hass.states[e]?.attributes.friendly_name??e}"
                  @click=${()=>this._setLuxSensors(r.filter(t=>t!==e))}>
                  <ha-icon icon="mdi:close"></ha-icon>
                </button>
              </span>
            `)}
            ${this._addingLux?L:F`
              <button class="chip chip-add" @click=${()=>{this._selectedLux=new Set,this._addingLux=!0}}>
                <ha-icon icon="mdi:plus"></ha-icon>${V(`lux.sensor_chip`,n)}
              </button>`}
          </div>
          ${r.length===0&&!this._addingLux?F`<p class="empty-hint" style="padding: var(--vr-space-1) 0 0">${V(`room.lux_none`,n)}</p>`:L}
          ${this._addingLux?this._renderMultiChooser({available:U(this.hass,e.area_id,`sensor`,[`illuminance`]).filter(e=>!r.includes(e)),selected:()=>this._selectedLux,icon:()=>`mdi:brightness-5`,emptyText:V(`room.area_no_lux`,n),onChange:e=>{this._selectedLux=e},onCancel:()=>{this._addingLux=!1},onConfirm:e=>{this._setLuxSensors([...r,...e.filter(e=>!r.includes(e))]),this._addingLux=!1,this._selectedLux=new Set}}):L}

          ${r.length>1?F`
            <div class="alarm-sub">${V(`lux.mode_question`,n)}</div>
            <div class="alarm-options lux-modes" role="radiogroup" aria-label=${V(`lux.mode_question`,n)}>
              ${ot.map(e=>F`
                <button class="alarm-opt ${o===e?`selected`:``}" role="radio" aria-checked=${o===e?`true`:`false`}
                  title=${V(`lux.mode_${e}_hint`,n)}
                  @click=${()=>this._patch({lux_mode:e})}>
                  <ha-icon icon=${p[e]}></ha-icon>
                  <span class="alarm-opt-title">${V(`lux.mode_${e}`,n)}</span>
                  <span class="alarm-opt-hint">${f(st(a,e))}</span>
                </button>`)}
            </div>
            <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`lux.mode_${o}_hint`,n)}</p>
          `:L}

          ${r.length>0?F`
            <div class="alarm-sub">${V(`lux.dark_title`,n)}</div>
            <div class="target-lux-row" style="margin-top: 0">
              <ha-icon icon="mdi:weather-night"></ha-icon>
              <input type="range" min="0" max="1000" step="10" aria-label=${V(`lux.dark_title`,n)}
                .value=${String(Math.min(s,1e3))}
                @input=${e=>this._patch({dark_lux:Number(e.target.value)})} />
              ${this._num(s,0,1e5,`lx`,V(`lux.dark_title`,n),e=>this._patch({dark_lux:e}),s>0?L:F`<span class="slider-extra">${V(`lux.always`,n)}</span>`)}
            </div>
            <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">
              <span class="info-text">${s>0?V(`lux.dark_hint`,n).replace(`{lux}`,String(s)):V(`lux.dark_hint_always`,n)}</span>
            </p>

            <div class="alarm-sub">${V(`lux.control_title`,n)}</div>
            <div class="alarm-options" role="radiogroup" aria-label=${V(`lux.control_title`,n)}>
              <button class="alarm-opt ${u?``:`selected`}" role="radio" aria-checked=${u?`false`:`true`}
                @click=${()=>this._patch({target_lux_enabled:!1})}>
                <ha-icon icon="mdi:circle-off-outline"></ha-icon>
                <span class="alarm-opt-title">${V(`lux.target_off_title`,n)}</span>
                <span class="alarm-opt-hint">${V(`lux.target_off_card`,n)}</span>
              </button>
              <button class="alarm-opt ${u?`selected`:``}" role="radio" aria-checked=${u?`true`:`false`}
                @click=${()=>this._patch({target_lux_enabled:!0,target_lux:d})}>
                <ha-icon icon="mdi:target"></ha-icon>
                <span class="alarm-opt-title">${V(`lux.target_on_title`,n)}</span>
                <span class="alarm-opt-hint">${V(`lux.target_on_card`,n)}</span>
              </button>
            </div>
            ${u?F`
              <div class="target-lux-row">
                <ha-icon icon="mdi:brightness-5"></ha-icon>
                <input type="range" min="10" max="1000" step="10" aria-label=${V(`room.target_lux`,n)}
                  .value=${String(Math.min(d,1e3))}
                  @input=${this._onTargetLuxInput} />
                ${this._num(d,1,1e5,`lx`,V(`room.target_lux`,n),e=>this._patch({target_lux:e}))}
              </div>
              <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`lux.target_on_hint`,n)}</p>
              ${this._renderLuxAlarmPause(e)}
            `:L}

            <div class="alarm-summary">${h}</div>
          `:L}
        </div>
        `:this._foldSummary(`lux`,h)}
      </div>
    `}_renderHaName(e,t,n,r){let i=this.hass.language,a=V(t===`lights_name`?`ha_name.label_lights`:`ha_name.label`,i),o=this.hass.areas?.[e.area_id]?.name??e.name,s=e[t]??``,c=[o,s.trim()||n].filter(Boolean).join(` `);return F`
      <div class="picker-card" style="margin-top: var(--vr-space-2)">
        <label class="ha-name">
          <ha-icon icon=${r}></ha-icon>
          <span class="fixed-label">${a}</span>
          <input
            class="group-name"
            .value=${s}
            placeholder=${n||o}
            aria-label=${a}
            @input=${e=>this._patch({[t]:e.target.value})}
          />
        </label>
        <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">
          ${V(`ha_name.hint`,i)} <strong>${c}</strong>
        </p>
      </div>
    `}_renderDefaultBrightness(e){let t=this.hass.language,n=e.default_brightness??0;return F`
      <div class="picker-card" style="margin-top: var(--vr-space-2)">
        <div class="chooser-caption">${V(`lux.default_title`,t)}</div>
        <div class="target-lux-row" style="margin-top: 0">
          <ha-icon icon="mdi:lightbulb-on-50"></ha-icon>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            aria-label=${V(`lux.default_title`,t)}
            .value=${String(n)}
            @input=${e=>this._patch({default_brightness:Number(e.target.value)})}
          />
          ${this._num(n,0,100,`%`,V(`lux.default_title`,t),e=>this._patch({default_brightness:e}),n>0?L:F`<span class="slider-extra">${V(`lux.not_set`,t)}</span>`)}
        </div>
        <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`lux.default_hint`,t)}</p>
      </div>
    `}_onTargetLuxInput(e){if(!this._draft)return;let t=Number(e.target.value);this._draft={...this._draft,target_lux:t}}_onSchedulePicked(e){let t=e.detail.value;if(!t||!this._draft)return;let n=this._draft.schedules??[];n.includes(t)||(this._draft={...this._draft,schedules:[...n,t]}),this._addingSchedule=!1}_removeSchedule(e){if(!this._draft)return;let t=[...this._draft.schedules??[]];t.splice(e,1),this._draft={...this._draft,schedules:t,...t.length<=1?{schedule_selector:``}:{}}}_onSelectorPicked(e){let t=e.detail.value;t&&this._setSelector(t)}_setSelector(e){this._draft&&={...this._draft,schedule_selector:e}}async _toggleDim(){this._draft&&(await this._flushSave(),await Re(this.hass,!mt(this.hass,this._draft.area_id),this._draft.area_id))}_togglePerson(e){if(!this._draft)return;let t=this._draft.persons??[];this._draft={...this._draft,persons:t.includes(e)?t.filter(t=>t!==e):[...t,e]}}_setFollowDaylight(e){if(!this._draft)return;let t=e&&this._draft.daylight_lights===void 0?[]:this._draft.daylight_lights;this._draft={...this._draft,follow_daylight:e,daylight_lights:t}}_renderDaylightColour(e){let t=this.hass.language,n=e.daylight_min_kelvin??2200,r=e.daylight_max_kelvin??5e3,i=e.lights.map(e=>e.entity_id).filter(e=>!!(this.hass.states[e]?.attributes.supported_color_modes)?.some(e=>[`hs`,`xy`,`rgb`,`rgbw`,`rgbww`].includes(e))),a=e=>{let[t,n,r]=pt(e);return F`<span class="swatch" style="background: rgb(${t}, ${n}, ${r})"></span>`};return F`
      <div class="picker-card" style="margin-top: var(--vr-space-2)">
        <label class="chooser-row" style="padding: 0">
          <input
            type="checkbox"
            .checked=${!!e.daylight_prefer_rgb}
            ?disabled=${i.length===0}
            @change=${e=>this._patch({daylight_prefer_rgb:e.target.checked})}
          />
          <span class="chooser-name" style="white-space: normal">
            ${V(`daylight.rgb_title`,t)}
            <span class="light-state" style="display:block">
              ${i.length===0?V(`daylight.rgb_none`,t):F`<span class="info-text">${V(`daylight.rgb_hint`,t)}</span>`}
            </span>
          </span>
        </label>
        <div class="target-lux-row">
          <span class="fixed-label">${V(`daylight.warmest`,t)}</span>
          <input
            type="range" min="1500" max="3500" step="100"
            aria-label=${V(`daylight.warmest`,t)}
            .value=${String(n)}
            @input=${e=>this._patch({daylight_min_kelvin:Number(e.target.value)})}
          />
          ${this._num(n,1500,3500,`K`,V(`daylight.warmest`,t),e=>this._patch({daylight_min_kelvin:e}),a(n))}
        </div>
        <div class="target-lux-row">
          <span class="fixed-label">${V(`daylight.coolest`,t)}</span>
          <input
            type="range" min="3500" max="6500" step="100"
            aria-label=${V(`daylight.coolest`,t)}
            .value=${String(r)}
            @input=${e=>this._patch({daylight_max_kelvin:Number(e.target.value)})}
          />
          ${this._num(r,3500,6500,`K`,V(`daylight.coolest`,t),e=>this._patch({daylight_max_kelvin:e}),a(r))}
        </div>
      </div>
    `}_supportsKelvin(e){return!!(this.hass.states[e]?.attributes.supported_color_modes)?.some(e=>[`color_temp`,`hs`,`xy`,`rgb`,`rgbw`,`rgbww`].includes(e))}_renderDaylightLamps(e){let t=this.hass.language;if(e.lights.length===0)return F`<p class="empty-hint" style="padding-bottom: 0">${V(`room.daylight_no_lights`,t)}</p>`;let n=e.daylight_lights??e.lights.map(e=>e.entity_id).filter(e=>this._supportsKelvin(e)),r=n.some(t=>e.lights.some(e=>e.entity_id===t)&&this._supportsKelvin(t));return F`
      <div class="picker-card chooser" style="margin-top: var(--vr-space-2)">
        <div class="chooser-caption">${V(`room.daylight_lamps`,t)}</div>
        ${e.lights.map(({entity_id:e})=>{let r=this.hass.states[e]?.attributes.friendly_name??e,i=this._supportsKelvin(e);return F`
            <label class="chooser-row ${i?``:`disabled`}" title=${e}>
              <input
                type="checkbox"
                .checked=${i&&n.includes(e)}
                ?disabled=${!i}
                @change=${()=>this._toggleDaylightLamp(e,n)}
              />
              <ha-icon
                icon=${i?`mdi:lightbulb-on-outline`:`mdi:lightbulb-outline`}
                style="--mdc-icon-size:18px; color: ${i?`var(--vr-on)`:`var(--secondary-text-color)`}"
              ></ha-icon>
              <span class="chooser-name">${r}</span>
              ${i?L:F`<span class="light-state">${V(`room.daylight_not_capable`,t)}</span>`}
            </label>
          `})}
      </div>
      ${r?L:F`<p class="required-hint" role="alert">
            <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
            ${V(`room.daylight_pick_required`,t)}
          </p>`}
    `}_toggleDaylightLamp(e,t){if(!this._draft)return;let n=t.includes(e)?t.filter(t=>t!==e):[...t,e];this._draft={...this._draft,daylight_lights:n}}_alarmPanels(){return Object.keys(this.hass.states).filter(e=>e.startsWith(`alarm_control_panel.`)).sort()}_toggleClockFold(e){let t=new Set(this._clockFolds);t.has(e)?t.delete(e):t.add(e),this._clockFolds=t}_clockFold(e,t,n,r,i){let a=`${e}:${t}`,o=this._clockFolds.has(a);return F`<div class="clock-fold">
      <button class="clock-fold-head" aria-expanded=${o?`true`:`false`} @click=${()=>this._toggleClockFold(a)}>
        <span class="clock-fold-title">${n}<ha-icon icon=${o?`mdi:chevron-up`:`mdi:chevron-down`}></ha-icon></span>
        ${o?L:r}
      </button>
      ${o?F`<div class="clock-fold-body">${i()}</div>`:L}
    </div>`}_clockPill(e,t,n=``){return F`<span class="clock-pill ${n}"><ha-icon icon=${e}></ha-icon>${t}</span>`}_setClock(e,t){this._draft&&this._patch({alarm_clocks:(this._draft.alarm_clocks??[]).map(n=>n.id===e?{...n,...t}:n)})}_addClock(e){let t=e.alarm_clocks??[],n=``;do n=`w${Date.now().toString(36)}${Math.random().toString(36).slice(2,5)}`;while(t.some(e=>e.id===n));let r=(e.media_players??[]).length>0?[]:this._clockPlayers(e.area_id),i={id:n,name:``,time:`07:00`,days:[0,1,2,3,4],enabled:!0,bundles:(e.groups??[]).map(e=>e.id),snooze:!1,snoozes:3,snooze_minutes:5,music:!1,volume_start:10,volume_end:35,stop_music:!0,stop_light:!1,...r.length===1?{media_player:r[0]}:{}};this._patch({alarm_clocks:[...t,i]}),this._openClocks=new Set([...this._openClocks,n])}_clockPlayers(e){let t=U(this.hass,e,`media_player`),n=Object.keys(this.hass.states).filter(e=>e.startsWith(`media_player.`)&&!t.includes(e)).filter(e=>ln.includes(this.hass.entities?.[e]?.platform??``)).filter(e=>!Ye(this.hass,e)).sort();return[...t,...n]}static _addMinutes(e,t){let[n,r]=e.split(`:`).map(Number),i=((n*60+r+t)%1440+1440)%1440;return`${String(Math.floor(i/60)).padStart(2,`0`)}:${String(i%60).padStart(2,`0`)}`}_renderClocks(e){let t=this.hass.language,n=e.alarm_clocks??[],r=e.groups??[];if(r.length===0&&n.length===0)return L;let i=[0,1,2,3,4,5,6].map(e=>V(`clock.day_${e}`,t)),a=e=>e.once?V(`clock.once`,t):e.days.length===7?V(`clock.every_day`,t):[...e.days].sort().map(e=>i[e]).join(`, `)||V(`clock.no_days`,t),o=(e,n)=>e.name||`${V(`bundles.default_name`,t)} ${n+1}`;return F`
      <div class="section ${this._infoOpen(`clocks`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`clocks`,V(`clock.section`,t))}
          ${this._shown(`clocks`)?F`<button class="add-btn" @click=${()=>{this._setFull(`clocks`,!0),this._addClock(e)}}>
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:16px"></ha-icon>${V(`clock.add`,t)}
          </button>`:L}
        </div>
        ${this._infoText(`clocks`)}
        ${this._isOpen(`clocks`)?F`
          ${n.length===0?F`<p class="empty-hint">${V(`clock.none`,t)}</p>`:L}
          <div class="group-list">
            ${n.map(t=>this._renderClock(e,t,r,o,i,a(t)))}
          </div>
        `:this._foldItems(`clocks`,n.map(e=>{let n=e.enabled!==!1;return{icon:n?`mdi:alarm`:`mdi:alarm-off`,title:e.name||e.time,pills:[e.time,a(e)].filter(Boolean),status:V(n?`card.on`:`card.off`,t),tone:n?`ok`:``}}),V(`clock.none`,t))}
      </div>
    `}_renderClockSteps(e,t,n){let r=this.hass.language,i=t=>this._setClock(e.id,t),a=`${e.id}:stop`,o=this._clockFolds.has(a),s=V(n.stopMusic&&n.stopLight?`clock.stop_what_both`:n.stopMusic?`clock.stop_what_music`:n.stopLight?`clock.stop_what_light`:`clock.stop_what_none`,r),c=(e,t,n)=>F`
      <button class="clock-check ${e?`on`:``}" role="checkbox" aria-checked=${e?`true`:`false`} @click=${()=>i(n)}>
        <ha-icon icon=${e?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>${t}
      </button>`;return F`
      <div class="clock-steps clock-steps-row" style="grid-template-columns: repeat(${t.length+1}, minmax(84px, 1fr))">
        ${t.map(e=>F`
          <div class="clock-step">
            <span class="clock-step-at">${V(`clock.snooze_n`,r).replace(`{n}`,String(e.i+1))} · ${e.at}</span>
            <span class="clock-step-pct">${e.pct}%</span>
            <span class="clock-step-bar"><span style="width: ${e.pct}%"></span></span>
            ${n.coversAlong?F`<span class="clock-step-bar cover"><span style="width: ${e.pct}%"></span></span>`:L}
            ${n.music?F`<span class="clock-step-bar vol"><span style="width: ${n.stepVol(e.i)}%"></span></span>`:L}
          </div>`)}
        <div class="clock-step">
          <button class="clock-stop-btn" aria-expanded=${o?`true`:`false`} @click=${()=>this._toggleClockFold(a)}>
            ${V(`clock.stop_step`,r)} · ${n.stopAt}<ha-icon icon=${o?`mdi:chevron-up`:`mdi:chevron-down`}></ha-icon>
          </button>
          <span class="clock-step-pct">${n.stopLight?V(`clock.pill_off`,r):`100%`}</span>
          <span class="clock-step-bar"><span style="width: ${n.stopLight?0:100}%"></span></span>
          ${n.coversAlong?F`<span class="clock-step-bar cover"><span style="width: 100%"></span></span>`:L}
          ${n.music?F`<span class="clock-step-bar vol"><span style="width: ${n.stopMusic?0:n.v1}%"></span></span>`:L}
          ${o?F`${c(n.stopMusic,V(`clock.stop_music`,r),{stop_music:!n.stopMusic})}
                ${c(n.stopLight,V(`clock.stop_light`,r),{stop_light:!n.stopLight})}`:F`<span class="clock-step-at">${s}</span>`}
        </div>
      </div>`}_renderClock(e,t,n,r,i,a){let o=this.hass.language,s=this._openClocks.has(t.id),c=()=>{let e=new Set(this._openClocks);s?e.delete(t.id):e.add(t.id),this._openClocks=e},l=e=>this._setClock(t.id,e),u=n.filter(e=>t.bundles.includes(e.id)),d=e.media_players??[],f=d.length>0?d:this._clockPlayers(e.area_id),p=d.length>0?t.media_player&&d.includes(t.media_player)?t.media_player:d[0]:t.media_player,m=e=>ln.includes(this.hass.entities?.[e]?.platform??``),h=e=>{let t=this.hass.states[e]?.attributes.friendly_name??e;return m(e)?`${t} · Music Assistant`:t},g=t.media?.media_content_id?t.media.media_content_id.split(`/`).pop()||t.media.media_content_id:``,_=!!t.snooze,v=t.music??!!(p&&t.media?.media_content_id),y=v&&!!p&&!!t.media?.media_content_id,b=_?Math.max(0,Math.min(10,t.snoozes??3)):0,x=Array.from({length:b+1},(e,n)=>({i:n,pct:Math.round(100*(n+1)/(b+1)),at:X._addMinutes(t.time||`07:00`,n*(t.snooze_minutes??5))})),S=e.covers??[],C=!!t.covers_open&&S.length>0,ee=S,w=_&&t.covers_steps===`own`,T=w?Math.max(0,Math.min(10,t.covers_snoozes??3)):b,te=w?t.covers_snooze_minutes??5:t.snooze_minutes??5,E=Array.from({length:T+1},(e,n)=>({i:n,pct:Math.round(100*(n+1)/(T+1)),at:X._addMinutes(t.time||`07:00`,n*te)})),D=t.snooze_minutes??5,O=t.stop_music!==!1,k=!!t.stop_light,A=X._addMinutes(t.time||`07:00`,(b+1)*D),ne=V(O&&k?`clock.stop_what_both`:O?`clock.stop_what_music`:k?`clock.stop_what_light`:`clock.stop_what_none`,o),j=t.volume_start??10,M=t.volume_end??35,re=e=>Math.round(b===0?M:j+(M-j)*e/b),ie=[a,u.length?u.map(e=>r(e,n.indexOf(e))).join(`, `):V(`clock.no_bundles`,o),_?V(`clock.sub_snooze`,o).replace(`{n}`,String(b)):``,C&&ee.length?V(w?`clock.sub_covers_own`:`clock.sub_covers_same`,o):``,y?V(`clock.music`,o):``].filter(Boolean).join(` · `),ae=F`
      <div class="bundle-row ${s?`open`:``}" @click=${s?L:c}>
        <ha-icon class="bundle-icon ${t.enabled?`on`:``}" icon=${t.enabled?`mdi:alarm`:`mdi:alarm-off`}></ha-icon>
        <span class="clock-time ${t.enabled?``:`off`}">${t.time}</span>
        <div class="bundle-text">
          <span class="bundle-title">${t.name||V(`clock.default_name`,o)}</span>
          <span class="bundle-sub">${ie}</span>
        </div>
        ${this._moveCtl((()=>{let n=e.alarm_clocks??[],r=n.findIndex(e=>e.id===t.id);return{index:r,count:n.length,name:t.name||t.time,onMove:e=>this._patch({alarm_clocks:X._moved(n,r,e)})}})())}
        <span @click=${e=>e.stopPropagation()}>
          <vr-toggle .checked=${t.enabled} @change=${e=>l({enabled:e.detail.value})}></vr-toggle>
        </span>
        <button class="bundle-expand" aria-expanded=${s?`true`:`false`}
          aria-label=${V(s?`bundles.collapse`:`bundles.expand`,o)}
          @click=${e=>{e.stopPropagation(),c()}}>
          <ha-icon icon=${s?`mdi:chevron-up`:`mdi:chevron-down`}></ha-icon>
        </button>
      </div>`;if(!s)return F`<div class="bundle-card">${ae}</div>`;let N=t.persons??[],oe=this.settings.clock_persons??this.enabledPersons,P=this.enabledPersons.filter(e=>oe.includes(e)||N.includes(e)),se=(e.persons??[]).filter(e=>this.enabledPersons.includes(e)),ce=e=>this.hass.states[e]?.attributes.friendly_name??e,le=u.length?u.map(e=>r(e,n.indexOf(e))).join(`, `):V(`clock.no_bundles`,o),ue=(_?V(`clock.summary`,o).replace(`{first}`,String(x[0].pct)).replace(`{n}`,String(b)).replace(`{min}`,String(t.snooze_minutes??5)):V(`clock.summary_direct`,o)).replace(`{days}`,a.toLowerCase()).replace(`{time}`,t.time).replace(`{bundles}`,le)+(y?` ${V(`clock.summary_music`,o).replace(`{player}`,h(p))}`:``)+` ${O||k?V(`clock.summary_stop`,o).replace(`{time}`,A).replace(`{what}`,ne):V(`clock.summary_no_stop`,o)}`;return F`
      <div class="bundle-card open">
        ${ae}
        <div class="bundle-body">
          <div class="clock-line">
            <label class="clock-field">${V(`clock.time`,o)}
              <input type="time" class="clock-input" .value=${t.time}
                @change=${e=>{let t=e.target.value;t&&l({time:t})}} />
            </label>
            <label class="clock-field" style="flex: 1">${V(`clock.name`,o)}
              <input class="clock-input" style="width: 100%" .value=${t.name} placeholder=${V(`clock.default_name`,o)}
                @input=${e=>l({name:e.target.value})} />
            </label>
          </div>

          <div class="alarm-sub">${V(`clock.days`,o)}</div>
          <div class="chip-row">
            ${i.map((e,n)=>F`
              <button class="chip chip-day ${!t.once&&t.days.includes(n)?`on`:``}" role="checkbox"
                aria-checked=${!t.once&&t.days.includes(n)?`true`:`false`}
                @click=${()=>l({once:!1,days:t.days.includes(n)?t.days.filter(e=>e!==n):[...t.days,n].sort()})}>
                ${e}</button>`)}
            <button class="chip chip-toggle ${t.once?`on`:``}" role="checkbox" aria-checked=${t.once?`true`:`false`}
              @click=${()=>l({once:!t.once})}>
              <ha-icon icon=${t.once?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>${V(`clock.once`,o)}
            </button>
          </div>
          <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`clock.days_hint`,o)}</p>

          <div class="alarm-sub">${V(`clock.persons`,o)}</div>
          ${P.length===0?F`<p class="empty-hint" style="padding: 0">${V(`clock.persons_none`,o)}</p>`:F`<div class="chip-row">
                ${P.map(e=>F`
                  <button class="chip chip-toggle ${N.includes(e)?`on`:``}" role="checkbox"
                    aria-checked=${N.includes(e)?`true`:`false`}
                    @click=${()=>l({persons:N.includes(e)?N.filter(t=>t!==e):[...N,e]})}>
                    <ha-icon icon=${N.includes(e)?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
                    ${ce(e)}
                  </button>`)}
              </div>
              <p class="empty-hint" style="padding: var(--vr-space-1) 0 0">${N.length?V(`clock.persons_chosen`,o):se.length?V(`clock.persons_room`,o).replace(`{names}`,se.map(ce).join(`, `)):V(`clock.persons_anyone`,o)}</p>`}

          ${this._clockFold(t.id,`bundles`,V(`clock.bundles`,o),u.length?u.map(e=>this._clockPill(`mdi:lightbulb-outline`,r(e,n.indexOf(e)),`light`)):[this._clockPill(`mdi:lightbulb-off-outline`,V(`clock.no_bundles`,o),`off`)],()=>F`
          <div class="chip-row">
            ${n.map((e,n)=>F`
              <button class="chip chip-toggle ${t.bundles.includes(e.id)?`on`:``}" role="checkbox"
                aria-checked=${t.bundles.includes(e.id)?`true`:`false`}
                @click=${()=>l({bundles:t.bundles.includes(e.id)?t.bundles.filter(t=>t!==e.id):[...t.bundles,e.id]})}>
                <ha-icon icon=${t.bundles.includes(e.id)?`mdi:checkbox-marked`:`mdi:checkbox-blank-outline`}></ha-icon>
                ${r(e,n)}
              </button>`)}
          </div>`)}

          ${this._clockFold(t.id,`steps`,V(`clock.snooze`,o),[_?this._clockPill(`mdi:stairs-up`,V(`clock.pill_steps`,o).replace(`{n}`,String(b+1)),`light`):this._clockPill(`mdi:lightbulb-on-outline`,V(`clock.pill_direct`,o),`light`),_?this._clockPill(`mdi:timer-outline`,V(`clock.pill_every`,o).replace(`{min}`,String(D))):L,this._clockPill(`mdi:stop-circle-outline`,`${A} · ${ne}`,O||k?`stop`:`off`)],()=>F`
          <div class="cover-follow" style="margin-top: 0; padding-top: 0; border-top: none">
            <ha-icon icon="mdi:stairs-up" style="--mdc-icon-size:20px; flex: none; color: ${_?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
            <div class="dusk-text">
              <div class="dusk-title">${V(`clock.snooze_on`,o)}</div>
              <div class="alarm-opt-hint">${V(_?C?`clock.snooze_on_hint_covers`:`clock.snooze_on_hint`:C?`clock.snooze_off_hint_covers`:`clock.snooze_off_hint`,o)}</div>
            </div>
            <vr-toggle .checked=${_} @change=${e=>l({snooze:e.detail.value})}></vr-toggle>
          </div>
          ${_?F`
            ${C?F`
              <div class="chip-row" role="radiogroup" aria-label=${V(`clock.snooze`,o)} style="margin-top: var(--vr-space-2)">
                <button class="chip chip-toggle ${w?``:`on`}" role="radio" aria-checked=${w?`false`:`true`}
                  @click=${()=>l({covers_steps:`same`})}>
                  <ha-icon icon="mdi:link-variant"></ha-icon>${V(`clock.covers_same`,o)}
                </button>
                <button class="chip chip-toggle ${w?`on`:``}" role="radio" aria-checked=${w?`true`:`false`}
                  @click=${()=>l({covers_steps:`own`,covers_snoozes:t.covers_snoozes??b,covers_snooze_minutes:t.covers_snooze_minutes??t.snooze_minutes??5})}>
                  <ha-icon icon="mdi:tune-variant"></ha-icon>${V(`clock.covers_own`,o)}
                </button>
              </div>`:L}
            ${C&&w?F`<div class="clock-steps-label"><ha-icon icon="mdi:lightbulb-outline"></ha-icon>${V(`clock.steps_light`,o)}</div>`:L}
            <div class="clock-line" style="margin-top: var(--vr-space-2)">
              <span class="clock-field">${V(`clock.snoozes`,o)}
                ${this._num((t.snoozes??3)+1,2,11,``,V(`clock.snoozes`,o),e=>l({snoozes:e-1}))}</span>
              <span class="clock-field">${V(`clock.snooze_minutes`,o)}
                ${this._num(t.snooze_minutes??5,1,60,`min`,V(`clock.snooze_minutes`,o),e=>l({snooze_minutes:e}))}</span>
            </div>
          `:L}
            ${this._renderClockSteps(t,x,{coversAlong:C&&!w,music:y,stepVol:re,stopAt:A,stopMusic:O,stopLight:k,v1:M})}
            <div class="clock-legend">
              <span><span class="clock-legend-dot"></span>${V(`clock.steps_light`,o)}</span>
              ${C&&!w?F`<span><span class="clock-legend-dot cover"></span>${V(`clock.steps_covers`,o)}</span>`:L}
              ${y?F`<span><span class="clock-legend-dot vol"></span>${V(`clock.music_title`,o)}</span>`:L}
            </div>
            <p class="empty-hint ${O||k?`info-text`:`clock-warn`}" style="padding: var(--vr-space-1) 0 0">
              ${V(O||k?`clock.stop_hint`:`clock.stop_none_warn`,o)}</p>
          ${_?F`
            ${C&&w?F`
              <div class="clock-steps-label"><ha-icon icon="mdi:curtains"></ha-icon>${V(`clock.steps_covers`,o)}</div>
              <div class="clock-line" style="margin-top: var(--vr-space-2)">
                <span class="clock-field">${V(`clock.snoozes`,o)}
                  ${this._num((t.covers_snoozes??3)+1,1,11,``,V(`clock.snoozes`,o),e=>l({covers_snoozes:e-1}))}</span>
                <span class="clock-field">${V(`clock.snooze_minutes`,o)}
                  ${this._num(t.covers_snooze_minutes??5,1,60,`min`,V(`clock.snooze_minutes`,o),e=>l({covers_snooze_minutes:e}))}</span>
              </div>
              <div class="clock-steps">
                ${E.map(e=>F`
                  <div class="clock-step">
                    <span class="clock-step-at">${V(`clock.snooze_n`,o).replace(`{n}`,String(e.i+1))} · ${e.at}</span>
                    <span class="clock-step-pct">${e.pct}%</span>
                    <span class="clock-step-bar cover"><span style="width: ${e.pct}%"></span></span>
                  </div>`)}
              </div>`:L}
            <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`clock.snooze_hint`,o)}</p>
          `:L}`)}

          ${S.length>0?this._clockFold(t.id,`covers`,V(`clock.covers_title`,o),C?[this._clockPill(`mdi:curtains`,V(`clock.pill_open`,o),`cover`),this._clockPill(_?w?`mdi:tune-variant`:`mdi:link-variant`:`mdi:arrow-expand-horizontal`,V(_?w?`clock.pill_covers_own`:`clock.pill_covers_same`:`clock.pill_covers_direct`,o),`cover`)]:[this._clockPill(`mdi:curtains-closed`,V(`clock.pill_off`,o),`off`)],()=>F`
          <div class="cover-follow" style="margin-top: 0; padding-top: 0; border-top: none">
            <ha-icon icon="mdi:curtains" style="--mdc-icon-size:20px; flex: none; color: ${C?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
            <div class="dusk-text">
              <div class="dusk-title">${V(`clock.covers_on`,o)}</div>
              <div class="alarm-opt-hint">${V(C?_?`clock.covers_on_hint`:`clock.covers_on_hint_direct`:`clock.covers_off_hint`,o)}</div>
            </div>
            <vr-toggle .checked=${C} @change=${e=>l({covers_open:e.detail.value})}></vr-toggle>
          </div>
          ${C?F`
            <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`clock.covers_hint`,o)}</p>
          `:L}`):L}

          ${this._clockFold(t.id,`music`,V(`clock.music_title`,o),y?[this._clockPill(`mdi:speaker`,h(p),`vol`),g?this._clockPill(`mdi:playlist-music`,g,`vol`):L,this._clockPill(`mdi:volume-high`,`${j} → ${M}%`,`vol`)]:[this._clockPill(`mdi:music-off`,V(v?`clock.pill_pick`:`clock.pill_off`,o),`off`)],()=>F`
          <div class="cover-follow" style="margin-top: 0; padding-top: 0; border-top: none">
            <ha-icon icon="mdi:music" style="--mdc-icon-size:20px; flex: none; color: ${v?`var(--primary-color)`:`var(--secondary-text-color)`}"></ha-icon>
            <div class="dusk-text">
              <div class="dusk-title">${V(`clock.music_on`,o)}</div>
              <div class="alarm-opt-hint">${V(v?y?`clock.music_on_hint`:`clock.music_pick`:`clock.music_off_hint`,o)}</div>
            </div>
            <vr-toggle .checked=${v} @change=${e=>l({music:e.detail.value})}></vr-toggle>
          </div>
          ${v?f.length===0?F`<p class="empty-hint" style="padding: var(--vr-space-2) 0 0">${V(`clock.no_players`,o)}</p>`:F`
              ${d.length===1?F`<p class="empty-hint" style="padding: var(--vr-space-2) 0 0">
                    ${V(`clock.player_room`,o).replace(`{player}`,h(d[0]))}</p>`:F`
              <div class="clock-line">
                <label class="clock-field" style="flex: 1; margin-top: var(--vr-space-2)">${V(`clock.player`,o)}
                  <select class="clock-input" style="width: 100%"
                    @change=${e=>{let t=e.target.value;l({media_player:t||void 0,...t?{}:{media:void 0}})}}>
                    ${d.length===0?F`<option value="" ?selected=${!p}>${V(`clock.pick_player`,o)}</option>`:L}
                    ${f.map(e=>F`<option value=${e} ?selected=${p===e}>${h(e)}</option>`)}
                  </select>
                </label>
              </div>
              ${d.length>1?F`<p class="empty-hint" style="padding: var(--vr-space-1) 0 0">${V(`clock.player_room_many`,o)}</p>`:L}`}
              ${p?F`
                <ha-selector
                  .hass=${this.hass}
                  .selector=${{media:{}}}
                  .value=${{entity_id:p,...t.media??{}}}
                  .label=${V(`clock.media`,o)}
                  @value-changed=${e=>{let t=e.detail.value;t?.media_content_id&&l({media:{media_content_id:t.media_content_id,media_content_type:t.media_content_type??`music`}})}}
                ></ha-selector>
                ${g?F`<p class="empty-hint" style="padding: var(--vr-space-1) 0 0">${V(`clock.media_chosen`,o)}: <strong>${g}</strong></p>`:L}
                <div class="clock-line" style="margin-top: var(--vr-space-2)">
                  <span class="clock-field">${V(`clock.volume_first`,o)}
                    ${this._num(j,0,100,`%`,V(`clock.volume_first`,o),e=>l({volume_start:e}))}</span>
                  <span class="clock-field">${V(`clock.volume_last`,o)}
                    ${this._num(M,0,100,`%`,V(`clock.volume_last`,o),e=>l({volume_end:e}))}</span>
                </div>`:L}`:L}`)}

          <p class="empty-hint info-text" style="padding: var(--vr-space-1) 0 0">${V(`clock.ha_hint`,o)}</p>

          <div class="alarm-summary">
            ${ue}
            <button class="link-btn danger-link" @click=${()=>this._patch({alarm_clocks:(e.alarm_clocks??[]).filter(e=>e.id!==t.id)})}>
              ${V(`clock.delete`,o)}
            </button>
          </div>
        </div>
      </div>
    `}_renderAlarm(e){let t=this.hass.language,n=this.settings.alarm_entity||``,r=e.alarm_entity||n,i=G(this.hass,e.area_id)?.attributes.alarm_last_off,a=r?this.hass.states[r]?.state:void 0,o=e=>{if(!e)return`—`;let n=`alarm_state.${e}`,r=V(n,t);return r===n?e:r},s=r?this.hass.states[r]?.attributes.friendly_name??r:``,c=!!e.away_follow_schedule,l=e.armed_home_mode===`no_motion`,u=[{id:`motion`,icon:`mdi:motion-sensor`,title:`alarm.home_motion`,hint:`alarm.fixed_home`},{id:`no_motion`,icon:`mdi:gesture-tap`,title:`alarm.home_no_motion`,hint:`alarm.fixed_home_no_motion`}],d=[{follow:!1,icon:`mdi:lightbulb-off-outline`,title:`alarm.away_off`,hint:`alarm.fixed_away`},{follow:!0,icon:`mdi:calendar-clock`,title:`alarm.away_follow`,hint:`alarm.fixed_away_ignored`}],f=[{state:`disarmed`,icon:`mdi:shield-off-outline`,text:V(`alarm.fixed_disarmed`,t)},{state:`armed_home`,icon:`mdi:shield-home-outline`,text:V(l?`alarm.fixed_home_no_motion`:`alarm.fixed_home`,t)},{state:`armed_away`,icon:`mdi:shield-lock-outline`,text:V(c?`alarm.fixed_away_ignored`:`alarm.fixed_away`,t)}],p=f.find(e=>e.state===a),m=r?p?`${V(`alarm.now`,t)}: ${p.text}`:V(`alarm.fixed_other`,t):V(`alarm.panel_none`,t);return F`
      <div class="section ${this._infoOpen(`alarm`)?`show-info`:``}">
        <div class="section-header">
          ${this._foldTitle(`alarm`,V(`room.alarm_section`,t))}
          ${r?F`
            <span class="alarm-pill ${a===`armed_home`||a===`armed_away`?`armed`:``}">
              ${V(`alarm.now`,t)}: ${o(a)}
            </span>`:L}
        </div>
        ${this._infoText(`alarm`)}
        ${this._isOpen(`alarm`)?F`
        <div class="alarm-card">
          <p class="alarm-panel" style="margin-top: 0">
            ${r?F`${s} · ${e.alarm_entity?V(`alarm.panel_own`,t):V(`alarm.panel_general`,t)}`:V(`alarm.panel_none`,t)}
            ${e.alarm_entity?F`<button class="link-btn" @click=${()=>{this._clearAlarm(),this._pickingAlarm=!1}}>
                  ${V(n?`alarm.panel_use_general`:`alarm.panel_remove`,t)}</button>`:F`<button class="link-btn" @click=${()=>{this._pickingAlarm=!this._pickingAlarm}}>
                  ${V(`alarm.panel_pick_other`,t)}</button>`}
          </p>
          ${this._pickingAlarm?this._renderAreaPicker(this._alarmPanels(),V(`room.alarm_pick`,t),V(`room.alarm_none`,t),e=>{this._onAlarmPicked(e),this._pickingAlarm=!1},`margin: 0 0 var(--vr-space-3)`):L}

          <div class="alarm-fixed">
            ${f.map(e=>F`
              <div class="alarm-fixed-row ${a===e.state?`now`:``}">
                <ha-icon icon=${e.icon}></ha-icon>
                <div>
                  <div class="alarm-opt-title">${o(e.state)}${a===e.state?F` <span class="alarm-tab-now">· ${V(`alarm.now`,t).toLowerCase()}</span>`:L}</div>
                  ${e.state===`armed_home`?F`
                    <div class="alarm-opt-hint">${V(`alarm.home_choose`,t)}</div>
                    <div class="alarm-options alarm-home-modes" role="radiogroup" aria-label=${o(e.state)}>
                      ${u.map(e=>{let n=e.id===`no_motion`===l;return F`
                          <button class="alarm-opt ${n?`selected`:``}" role="radio"
                            aria-checked=${n?`true`:`false`}
                            @click=${()=>this._patch({armed_home_mode:e.id})}>
                            <span class="alarm-opt-title alarm-opt-head"><ha-icon icon=${e.icon}></ha-icon>${V(e.title,t)}</span>
                            <span class="alarm-opt-hint">${V(e.hint,t)}</span>
                          </button>`})}
                    </div>`:e.state===`armed_away`?F`
                    <div class="alarm-opt-hint">${V(`alarm.away_choose`,t)}</div>
                    <div class="alarm-options alarm-home-modes" role="radiogroup" aria-label=${o(e.state)}>
                      ${d.map(e=>{let n=e.follow===c;return F`
                          <button class="alarm-opt ${n?`selected`:``}" role="radio"
                            aria-checked=${n?`true`:`false`}
                            @click=${()=>this._patch({away_follow_schedule:e.follow})}>
                            <span class="alarm-opt-title alarm-opt-head"><ha-icon icon=${e.icon}></ha-icon>${V(e.title,t)}</span>
                            <span class="alarm-opt-hint">${V(e.hint,t)}</span>
                          </button>`})}
                    </div>`:F`<div class="alarm-opt-hint">${e.text}</div>`}
                </div>
              </div>`)}
          </div>
          ${r?F`<div class="alarm-summary">
            ${i?F`${V(`alarm.last_off`,t)} ${new Date(i).toLocaleString(t,{weekday:`short`,hour:`2-digit`,minute:`2-digit`})}`:V(`alarm.never_off`,t)}
          </div>`:L}
        </div>
        `:this._foldSummary(`alarm`,m)}
      </div>
    `}_onAlarmPicked(e){let t=e.detail.value;t&&this._draft&&(this._draft={...this._draft,alarm_entity:t})}_clearAlarm(){this._draft&&={...this._draft,alarm_entity:``}}async _save(){if(!this._draft)return;this._saveState=`saving`;let e=this._draft;try{let t=et(this.hass,this.allRooms,e);await Ie(this.hass,{rooms:t}),this.dispatchEvent(new CustomEvent(`room-saved`,{detail:{room:e,rooms:t},bubbles:!0,composed:!0})),this._saveTimer===void 0&&(this._saveState=`saved`,window.clearTimeout(this._savedTimer),this._savedTimer=window.setTimeout(()=>{this._saveState===`saved`&&(this._saveState=`idle`)},3e3))}catch{this._saveState=`error`}}};q([z({attribute:!1})],Q.prototype,`hass`,void 0),q([z({attribute:!1})],Q.prototype,`room`,void 0),q([z({attribute:!1})],Q.prototype,`allRooms`,void 0),q([z({attribute:!1})],Q.prototype,`enabledPersons`,void 0),q([z({attribute:!1})],Q.prototype,`settings`,void 0),q([B()],Q.prototype,`_draft`,void 0),q([B()],Q.prototype,`_saveState`,void 0),q([B()],Q.prototype,`_brightness`,void 0),q([B()],Q.prototype,`_tab`,void 0),q([B()],Q.prototype,`_addingLight`,void 0),q([B()],Q.prototype,`_selectedLights`,void 0),q([B()],Q.prototype,`_addingMotion`,void 0),q([B()],Q.prototype,`_addingLinks`,void 0),q([B()],Q.prototype,`_selectedLinks`,void 0),q([B()],Q.prototype,`_selectedMotion`,void 0),q([B()],Q.prototype,`_addingLux`,void 0),q([B()],Q.prototype,`_selectedLux`,void 0),q([B()],Q.prototype,`_addingSchedule`,void 0),q([B()],Q.prototype,`_debugOpen`,void 0),q([B()],Q.prototype,`_debugEntries`,void 0),q([B()],Q.prototype,`_debugNow`,void 0),q([B()],Q.prototype,`_closedSections`,void 0),q([B()],Q.prototype,`_fullSections`,void 0),q([B()],Q.prototype,`_openInfos`,void 0),q([B()],Q.prototype,`_editingFans`,void 0),q([B()],Q.prototype,`_addingFans`,void 0),q([B()],Q.prototype,`_fanSelection`,void 0),q([B()],Q.prototype,`_addingFanShare`,void 0),q([B()],Q.prototype,`_fanShareSelection`,void 0),q([B()],Q.prototype,`_openCovers`,void 0),q([B()],Q.prototype,`_coverTest`,void 0),q([B()],Q.prototype,`_addingLocks`,void 0),q([B()],Q.prototype,`_lockSelection`,void 0),q([B()],Q.prototype,`_openLocks`,void 0),q([B()],Q.prototype,`_confirmLock`,void 0),q([B()],Q.prototype,`_addingCovers`,void 0),q([B()],Q.prototype,`_coverSelection`,void 0),q([B()],Q.prototype,`_addingMedia`,void 0),q([B()],Q.prototype,`_mediaSelection`,void 0),q([B()],Q.prototype,`_addingVacuum`,void 0),q([B()],Q.prototype,`_vacuumSelection`,void 0),q([B()],Q.prototype,`_openPlans`,void 0),q([B()],Q.prototype,`_vacuumBusy`,void 0),q([B()],Q.prototype,`_vacuumError`,void 0),q([B()],Q.prototype,`_addingDoor`,void 0),q([B()],Q.prototype,`_doorSelection`,void 0),q([B()],Q.prototype,`_bundleAdd`,void 0),q([B()],Q.prototype,`_bundleSel`,void 0),q([B()],Q.prototype,`_converting`,void 0),q([B()],Q.prototype,`_convertError`,void 0),q([B()],Q.prototype,`_openSlots`,void 0),q([B()],Q.prototype,`_openBundles`,void 0),q([B()],Q.prototype,`_groupEdit`,void 0),q([B()],Q.prototype,`_groupSelection`,void 0),q([B()],Q.prototype,`_groupNameDraft`,void 0),q([B()],Q.prototype,`_openClocks`,void 0),q([B()],Q.prototype,`_clockFolds`,void 0),q([B()],Q.prototype,`_pickingAlarm`,void 0),Q=X=q([ke(`vr-room-detail`)],Q);var fn=`M10,20V14H14V20H19V12H22L12,3L2,12H5V20H10Z`,pn=`M12,11A1,1 0 0,0 11,12A1,1 0 0,0 12,13A1,1 0 0,0 13,12A1,1 0 0,0 12,11M12.5,2C17,2 17.11,5.57 14.75,6.75C13.76,7.24 13.32,8.29 13.13,9.22C13.61,9.42 14.03,9.73 14.35,10.13C18.05,8.13 22.03,8.92 22.03,12.5C22.03,17 18.46,17.1 17.28,14.73C16.78,13.74 15.72,13.3 14.79,13.11C14.59,13.59 14.28,14 13.88,14.34C15.87,18.03 15.08,22 11.5,22C7,22 6.91,18.42 9.27,17.24C10.25,16.75 10.69,15.71 10.89,14.79C10.4,14.59 9.97,14.27 9.65,13.87C5.96,15.85 2,15.07 2,11.5C2,7 5.56,6.89 6.74,9.26C7.24,10.25 8.29,10.68 9.22,10.87C9.41,10.39 9.73,9.97 10.14,9.65C8.15,5.96 8.94,2 12.5,2Z`,mn={persons:[],group_by_floor:!1,alarm_entity:``,dim_on_armed_home:!1,sun_entity:`sun.sun`},$=class extends R{constructor(...e){super(...e),this.narrow=!1,this.panel={},this._config=null,this._loading=!0,this._error=``,this._view=`dashboard`,this._selectedAreaId=null,this._showHidden=!1,this._settingsSave=`idle`,this._dimBusy=!1,this._ovStacked=!1}async connectedCallback(){super.connectedCallback(),await this._loadConfig()}disconnectedCallback(){super.disconnectedCallback(),this._ovResize?.disconnect(),this._ovResize=void 0}updated(){let e=this.renderRoot.querySelectorAll(`[data-ov]`);!this._ovResize&&typeof ResizeObserver<`u`&&(this._ovResize=new ResizeObserver(()=>this._layoutOverview())),this._ovResize&&(this._ovResize.disconnect(),e.forEach(e=>this._ovResize.observe(e)))}_layoutOverview(){let e=e=>this.renderRoot.querySelector(`[data-ov="${e}"]`)?.offsetHeight??0,t=e(`active`),n=e(`standby`),r=e(`links`);if(!r||(this.renderRoot.querySelector(`.overview`)?.clientWidth??0)<620){this._ovStacked&&=!1;return}let i=t+n+12,a=this._ovStacked?i<=r*1.4:i<=r*1.1;a!==this._ovStacked&&(this._ovStacked=a)}async _loadConfig(){this._loading=!0,this._error=``;try{this._config=await Fe(this.hass)}catch{this._error=V(`panel.load_error`,this.hass.language)}finally{this._loading=!1}}static{this.styles=[Me,o`
      :host {
        display: block;
        min-height: 100%;
        background: var(--lovelace-background, var(--primary-background-color));
      }

      .header {
        display: flex;
        align-items: center;
        padding: var(--vr-space-4) var(--vr-space-5);
        border-bottom: 1px solid var(--vr-border);
        background: var(--app-header-background-color, var(--primary-background-color));
        position: sticky;
        top: 0;
        z-index: 1;
      }

      .header h1 {
        font-size: var(--vr-font-xl);
        font-weight: 500;
        color: var(--primary-text-color);
        margin: 0;
        flex: 1;
        display: flex;
        align-items: baseline;
        gap: var(--vr-space-2);
      }

      .header h1 .version {
        font-size: var(--vr-font-xs);
        font-weight: 400;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }

      .hidden-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
        background: none;
        border: 1px solid var(--vr-border);
        border-radius: 20px;
        padding: 4px 12px;
        cursor: pointer;
      }

      .hidden-btn.active {
        color: var(--primary-color);
        border-color: var(--primary-color);
        background: var(--vr-fill-primary);
      }

      .header {
        gap: var(--vr-space-2);
        flex-wrap: wrap;
      }

      .settings-btn {
        --mdc-icon-button-size: 40px;
        --mdc-icon-size: 22px;
        color: var(--primary-text-color);
      }

      .late-home {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--vr-space-2);
        margin-bottom: var(--vr-space-4);
      }

      .late-title {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: var(--vr-font-sm);
        font-weight: 500;
        color: var(--secondary-text-color);
        margin-right: var(--vr-space-1);
      }

      .late-title ha-icon, .late-btn ha-icon {
        --mdc-icon-size: 18px;
      }

      .late-btn {
        font: inherit;
        font-size: var(--vr-font-sm);
        display: inline-flex;
        align-items: center;
        gap: 6px;
        min-height: 36px;
        padding: 4px 12px;
        border: 1px solid var(--vr-border);
        border-radius: 999px;
        background: var(--vr-surface);
        color: var(--primary-text-color);
        cursor: pointer;
      }

      .late-btn.on {
        border-color: var(--primary-color);
        background: var(--vr-fill-primary);
        color: var(--primary-color);
      }

      .late-btn[disabled] {
        opacity: 0.55;
        cursor: not-allowed;
      }

      .late-state {
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
      }

      .overview-wrap {
        margin-bottom: var(--vr-space-5);
      }

      .ov-top {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: var(--vr-space-2);
        flex-wrap: wrap;
        margin-bottom: var(--vr-space-2);
      }

      .ov-title {
        font-size: var(--vr-font-md);
        font-weight: 500;
        color: var(--primary-text-color);
      }

      .ov-sub {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .ov-bar {
        height: 6px;
        border-radius: 3px;
        background: var(--vr-fill);
        overflow: hidden;
        margin-bottom: var(--vr-space-3);
      }

      .ov-bar span {
        display: block;
        height: 100%;
        background: var(--vr-on);
      }

      .overview {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: var(--vr-space-3);
        align-items: start;
      }

      /* Many links: Active + Standby stacked in one column, links in the other. */
      .overview.stacked {
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      }

      .ov-stack {
        display: grid;
        gap: var(--vr-space-3);
      }

      .ov-rows {
        display: grid;
        gap: 6px;
      }

      .ov-row {
        font: inherit;
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        padding: 6px 10px;
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        background: var(--vr-surface);
        color: var(--primary-text-color);
        font-size: var(--vr-font-sm);
        text-align: left;
        cursor: pointer;
      }

      .ov-row:hover {
        border-color: var(--vr-border-strong);
      }

      .ov-row ha-icon {
        --mdc-icon-size: 18px;
        color: var(--vr-on);
        flex: none;
      }

      .ov-row-name {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .ov-row-val {
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }

      .ov-link {
        padding: var(--vr-space-2) 0;
      }

      .ov-link + .ov-link {
        border-top: 1px solid var(--vr-border);
      }

      .ov-link-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--vr-space-2);
        margin-bottom: 6px;
      }

      .ov-link-count {
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
      }

      .ov-kind {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: var(--vr-font-xs);
        padding: 2px 8px;
        border-radius: 999px;
        white-space: nowrap;
      }

      .ov-kind ha-icon {
        --mdc-icon-size: 14px;
      }

      .ov-kind.motion {
        background: color-mix(in srgb, var(--vr-motion) 16%, transparent);
        color: var(--primary-text-color);
      }

      .ov-kind.fan {
        background: var(--vr-fill-primary);
        color: var(--primary-color);
      }

      .ov-chip.on {
        border-color: color-mix(in srgb, var(--vr-on) 50%, var(--vr-border));
      }

      .ov-diagram {
        display: block;
        width: 100%;
        max-width: 360px;
        height: auto;
        margin: 2px auto 0;
        overflow: visible;
      }

      .ov-floor-line {
        stroke: var(--vr-border);
        stroke-width: 1;
        stroke-dasharray: 2 4;
      }

      .ov-floor-label {
        font-size: 11px;
        fill: var(--secondary-text-color);
      }

      .ov-line {
        stroke: var(--vr-border-strong);
        stroke-width: 2;
      }

      .ov-line.fan {
        stroke: var(--primary-color);
        stroke-dasharray: 5 4;
      }

      .ov-node {
        cursor: pointer;
        outline: none;
      }

      .ov-node circle {
        fill: var(--vr-surface);
        stroke: var(--vr-border-strong);
        stroke-width: 2;
      }

      .ov-node.on circle {
        fill: var(--vr-on);
        stroke: var(--vr-on);
      }

      .ov-node:hover circle,
      .ov-node:focus-visible circle {
        stroke: var(--primary-color);
        stroke-width: 3;
      }

      .ov-node circle.ov-icon-bg {
        fill: var(--vr-surface);
        stroke: var(--vr-border);
        stroke-width: 1;
      }

      .ov-node.on circle.ov-icon-bg {
        fill: var(--vr-surface);
        stroke: var(--vr-on);
        stroke-width: 2;
      }

      .ov-icon {
        fill: var(--secondary-text-color);
        pointer-events: none;
      }

      .ov-node.on .ov-icon {
        fill: var(--vr-on);
      }

      .ov-node text {
        font-size: 12px;
        fill: var(--primary-text-color);
      }

      .ov-via {
        margin-top: 4px;
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
      }

      .ov-legend {
        display: grid;
        gap: 4px;
        margin-top: var(--vr-space-2);
        padding-top: var(--vr-space-2);
        border-top: 1px solid var(--vr-border);
        font-size: var(--vr-font-xs);
        color: var(--secondary-text-color);
      }

      .ov-group {
        background: var(--vr-surface);
        border: 1px solid var(--vr-border);
        border-radius: var(--vr-radius-sm);
        padding: var(--vr-space-3) var(--vr-space-4);
      }

      .ov-head {
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        margin-bottom: var(--vr-space-2);
      }

      .ov-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--vr-border-strong);
      }

      .ov-dot.active {
        background: var(--vr-on);
        box-shadow: 0 0 0 3px var(--vr-on-bg);
      }

      .ov-label {
        font-size: var(--vr-font-md);
        font-weight: 500;
        color: var(--primary-text-color);
        flex: 1;
      }

      .ov-count {
        font-size: var(--vr-font-xl);
        font-weight: 600;
        color: var(--primary-text-color);
        font-variant-numeric: tabular-nums;
      }

      .ov-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      .ov-chip {
        font: inherit;
        font-size: var(--vr-font-sm);
        padding: 4px 10px;
        border-radius: 14px;
        border: 1px solid var(--vr-border);
        background: var(--vr-fill);
        color: var(--primary-text-color);
        cursor: pointer;
      }

      .ov-chip:hover {
        border-color: var(--vr-border-strong);
      }

      .ov-none {
        font-size: var(--vr-font-sm);
        color: var(--secondary-text-color);
      }

      .floor-title {
        display: flex;
        align-items: center;
        gap: var(--vr-space-2);
        font-size: var(--vr-font-sm);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--secondary-text-color);
        margin: var(--vr-space-5) 0 var(--vr-space-3);
      }

      .floor-title:first-of-type {
        margin-top: 0;
      }

      .floor-title ha-icon {
        --mdc-icon-size: 18px;
      }

      .hidden-title {
        font-size: var(--vr-font-sm);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--secondary-text-color);
        margin: var(--vr-space-6) 0 var(--vr-space-3);
      }

      .content {
        padding: var(--vr-space-5);
        max-width: 900px;
        margin: 0 auto;
      }

      .grid {
        display: grid;
        /* never wider than the screen; a card's content wraps instead.
           auto-fill: every card the same width, also on a half-full last row */
        grid-template-columns: repeat(auto-fill, minmax(min(240px, 100%), 1fr));
        /* every row as tall as the tallest card: all cards the same height */
        grid-auto-rows: 1fr;
        gap: var(--vr-space-4);
      }

      .grid > * {
        min-width: 0;
      }

      :host([narrow]) .grid {
        grid-template-columns: 1fr;
      }

      .placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: var(--vr-space-3);
        padding: var(--vr-space-6) 0;
        color: var(--secondary-text-color);
        text-align: center;
      }

      .placeholder ha-icon {
        --mdc-icon-size: 48px;
        opacity: 0.4;
      }

      .placeholder p {
        font-size: var(--vr-font-lg);
        margin: 0;
      }

      .placeholder small {
        font-size: var(--vr-font-sm);
        opacity: 0.7;
      }

      .error-row {
        display: flex;
        align-items: center;
        gap: var(--vr-space-3);
        padding: var(--vr-space-4);
        background: color-mix(in srgb, var(--error-color) 10%, transparent);
        border-radius: var(--vr-radius);
        color: var(--error-color);
        font-size: var(--vr-font-md);
        margin-bottom: var(--vr-space-4);
      }

      .warn-row {
        display: flex;
        align-items: flex-start;
        gap: var(--vr-space-3);
        padding: var(--vr-space-3) var(--vr-space-4);
        background: color-mix(in srgb, var(--warning-color, #f59e0b) 14%, transparent);
        border: 1px solid color-mix(in srgb, var(--warning-color, #f59e0b) 50%, transparent);
        border-radius: var(--vr-radius);
        color: var(--primary-text-color);
        font-size: var(--vr-font-md);
        margin-bottom: var(--vr-space-4);
      }

      .warn-row ha-icon {
        color: var(--warning-color, #f59e0b);
      }

      .retry-btn {
        margin-left: auto;
        font-size: var(--vr-font-sm);
        color: var(--primary-color);
        background: none;
        border: 1px solid var(--primary-color);
        border-radius: var(--vr-radius-sm);
        padding: 4px 12px;
        cursor: pointer;
      }
    `]}render(){let e=this.hass.language;if(this._view===`room`&&this._selectedAreaId){let e=this._displayRooms().find(e=>e.area_id===this._selectedAreaId);if(e)return F`
          <vr-room-detail
            .hass=${this.hass}
            .room=${e}
            .allRooms=${this._config?.rooms??[]}
            .enabledPersons=${this._settings.persons}
            .settings=${this._settings}
            @back=${this._backToDashboard}
            @room-saved=${this._onRoomSaved}
          ></vr-room-detail>
        `}if(this._view===`settings`)return F`
        <vr-settings
          .hass=${this.hass}
          .settings=${this._settings}
          .rooms=${this._config?.rooms??[]}
          .textDefaults=${this._config?.text_defaults??{}}
          .saveState=${this._settingsSave}
          @back=${this._backToDashboard}
          @settings-changed=${e=>this._saveSettings(e.detail.settings)}
        ></vr-settings>
      `;let t=this._displayRooms(),n=t.filter(e=>!e.hidden),r=t.filter(e=>e.hidden),i=this._linkList(),a=Vt(this.hass,this._settings),o=e=>F`
      <div class="grid">
        ${e.map(e=>F`
            <vr-room-card
              .hass=${this.hass}
              .room=${e}
              .enabledPersons=${this._settings.persons}
              .links=${i.filter(t=>t.group.includes(e.area_id)).map(e=>({n:e.n,kind:e.kind}))}
              .phase=${hn(e)?a:null}
              @set-dim=${e=>this._dim(e.detail.dim,e.detail.areaId)}
              @set-manual=${e=>this._manual(e.detail.areaId,e.detail.minutes)}
              @open-room=${e=>this._openRoom(e.detail.areaId)}
              @set-hidden=${t=>this._setHidden(e,t.detail.hidden)}
            ></vr-room-card>
          `)}
      </div>
    `,s=(this._config?.rooms??[]).filter(e=>e.lights.length>0&&!e.hidden),c=s.length>0&&s.every(e=>mt(this.hass,e.area_id)),l=yt(this.hass);return F`
      ${l?.active?F`
        <div role="alert" style="display:flex;gap:12px;align-items:center;margin:0 0 var(--vr-space-3);padding:var(--vr-space-3);border-radius:var(--vr-radius-sm);background:color-mix(in srgb, var(--error-color, #db4437) 15%, transparent);border:1px solid var(--error-color, #db4437)">
          <ha-icon icon="mdi:fire-alert" style="--mdc-icon-size:28px;color:var(--error-color, #db4437);flex:none"></ha-icon>
          <div style="flex:1;min-width:0">
            <div style="font-weight:500;color:var(--error-color, #db4437)">${V(`smoke.banner_title`,e).replace(`{where}`,l.areas.map(e=>this.hass.areas?.[e]?.name??e).join(`, `)||`?`).replace(`{time}`,l.since?new Date(l.since).toLocaleTimeString(e,{hour:`2-digit`,minute:`2-digit`}):``)}</div>
            <div style="font-size:var(--vr-font-sm);color:var(--secondary-text-color)">${V(l.smoke_now.length?`smoke.banner_still`:`smoke.banner_hint`,e)}</div>
          </div>
          <button class="hidden-btn" @click=${()=>{this.hass.callWS({type:`roomcontrol/smoke_clear`})}}>
            <ha-icon icon="mdi:check" style="--mdc-icon-size:16px"></ha-icon>${V(`smoke.clear`,e)}
          </button>
        </div>`:L}
      <div class="header">
        <h1>
          ${V(`panel.title`,e)}
          <span class="version" title=${V(`panel.version`,e)}>v${this._config?.version??`1.17.1`}</span>
        </h1>
        ${s.length>0?F`
          <button
            class="hidden-btn ${c?`active`:``}"
            aria-pressed=${c}
            ?disabled=${this._dimBusy}
            title=${V(c?`dim.restore_all`:`dim.all_to_1`,e)}
            @click=${()=>this._dim(!c)}
          >
            <ha-icon icon="mdi:brightness-4" style="--mdc-icon-size:16px"></ha-icon>
            ${V(c?`dim.restore_all_short`:`dim.all_short`,e)}
          </button>
        `:L}
        ${r.length>0?F`
          <button
            class="hidden-btn ${this._showHidden?`active`:``}"
            aria-pressed=${this._showHidden}
            @click=${()=>{this._showHidden=!this._showHidden}}
          >
            <ha-icon icon=${this._showHidden?`mdi:eye`:`mdi:eye-off`} style="--mdc-icon-size:16px"></ha-icon>
            ${V(`panel.hidden_rooms`,e)} (${r.length})
          </button>
        `:L}
        <ha-icon-button
          class="settings-btn"
          .label=${V(`settings.title`,e)}
          .path=${`M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z`}
          @click=${()=>{this._view=`settings`}}
        ></ha-icon-button>
      </div>

      <div class="content">
        ${this._renderHealth()}
        ${this._error?F`
          <div class="error-row">
            <ha-icon icon="mdi:alert-circle-outline" style="--mdc-icon-size:20px; flex:none"></ha-icon>
            ${this._error}
            <button class="retry-btn" @click=${this._loadConfig}>
              ${V(`common.retry`,e)}
            </button>
          </div>
        `:L}

        ${this._loading?F`
          <div class="placeholder">
            <ha-icon icon="mdi:lightbulb-group"></ha-icon>
            <p>${V(`panel.loading`,e)}</p>
          </div>
        `:t.length===0?F`
          <div class="placeholder">
            <ha-icon icon="mdi:lightbulb-off-outline"></ha-icon>
            <p>${V(`panel.no_rooms`,e)}</p>
            <small>${V(`panel.no_rooms_hint`,e)}</small>
          </div>
        `:F`
          ${this._renderLateHome()}
          ${n.length>0?this._renderOverview(n):L}
          ${n.length>0?this._renderGrouped(n,o):F`
            <div class="placeholder">
              <ha-icon icon="mdi:eye-off-outline"></ha-icon>
              <p>${V(`panel.all_hidden`,e)}</p>
            </div>
          `}
          ${this._showHidden&&r.length>0?F`
            <h2 class="hidden-title">${V(`panel.hidden_rooms`,e)}</h2>
            ${o(r)}
          `:L}
        `}
      </div>
    `}_openRoom(e){this._selectedAreaId=e,this._view=`room`}_backToDashboard(){this._view=`dashboard`,this._selectedAreaId=null}_displayRooms(){return Je(this.hass,this._config?.rooms??[])}_withRoom(e){let t=this._config?.rooms??[];return t.some(t=>t.area_id===e.area_id)?t.map(t=>t.area_id===e.area_id?e:t):[...t,e]}get _settings(){return{...mn,...this._config?.settings??{}}}_onRoomSaved(e){let t=e.detail.rooms??this._withRoom(e.detail.room);this._config={...this._config,rooms:t}}async _saveSettings(e){let t=this._config;this._config={rooms:this._config?.rooms??[],settings:e},this._settingsSave=`saving`;try{await Le(this.hass,e),this._settingsSave=`saved`}catch{this._config=t,this._settingsSave=`error`}}async _manual(e,t){try{await ze(this.hass,e,t)}catch{this._error=V(`manual.error`,this.hass.language)}}async _dim(e,t){this._dimBusy=!0;try{await Re(this.hass,e,t)}catch{this._error=V(`dim.error`,this.hass.language)}finally{this._dimBusy=!1}}_renderHealth(){if(!this._config)return L;let e=this.hass.language,t=this._config.version,n=t===`1.17.1`?this._config.active===!1?V(`health.inactive`,e):null:V(`health.restart`,e).replace(`{running}`,t??V(`health.old`,e)).replace(`{expected}`,Kt);return n?F`<div class="warn-row" role="alert">
      <ha-icon icon="mdi:alert-outline" style="--mdc-icon-size:20px; flex:none"></ha-icon>
      <span>${n}</span>
    </div>`:L}_linkDiagram(e,t,n,r,i){let a=e.length,o=[];for(let n=0;n<a;n++)for(let r=n+1;r<a;r++)t(e[n],e[r])&&o.push([n,r]);let s=e.map((e,t)=>o.filter(([e,n])=>e===t||n===t).length),c=o.length===a-1&&s.every(e=>e<=2),l=(e,t)=>I`
      <circle class="ov-icon-bg" cx=${e} cy=${t} r="12"></circle>
      <path class="ov-icon" transform="translate(${e-10} ${t-10}) scale(0.8333)"
        d=${n===`fan`?pn:fn}></path>`,u=this.hass.floors??{},d=e=>{let t=this.hass.areas?.[e]?.floor_id;return t&&u[t]?t:``},f=[...new Set(e.map(d))];if(Object.keys(u).length>0&&f.length>1){let t=e=>e?u[e].level??0:-1/0,a=f.sort((e,n)=>t(e)-t(n)||(e?u[e].name:``).localeCompare(n?u[n].name:``)),s=320/a.length,c=a.map(t=>e.filter(e=>d(e)===t)),p=Math.max(...c.map(e=>e.length)),m=38+(p-1)*50+30,h=new Map;a.forEach((e,t)=>{let n=c[t],r=(p-n.length)*50/2;n.forEach((e,n)=>h.set(e,{x:s*(t+.5),y:38+r+n*50}))});let g=Math.max(6,Math.floor((s-8)/7)),_=e=>e.length>g?`${e.slice(0,g-1)}…`:e,v=e=>_(e?u[e].name:V(`floors.none`,this.hass.language));return F`<svg class="ov-diagram floors" viewBox="0 0 ${320} ${m}" role="img"
        aria-label=${a.map((e,t)=>`${v(e)}: ${c[t].map(r).join(`, `)}`).join(`; `)}>
        ${a.map((e,t)=>I`
          <text class="ov-floor-label" x=${s*(t+.5)} y=${16} text-anchor="middle">${v(e)}</text>
          ${t>0?I`<line class="ov-floor-line" x1=${s*t} y1="2" x2=${s*t} y2=${m}></line>`:L}`)}
        ${o.map(([t,r])=>{let i=h.get(e[t]),a=h.get(e[r]);return I`<line x1=${i.x} y1=${i.y} x2=${a.x} y2=${a.y} class="ov-line ${n}"></line>`})}
        ${e.map(e=>{let t=h.get(e);return I`<g class="ov-node ${i(e)?`on`:``}" tabindex="0" role="button"
            aria-label=${r(e)}
            @click=${()=>this._openRoom(e)}
            @keydown=${t=>{(t.key===`Enter`||t.key===` `)&&(t.preventDefault(),this._openRoom(e))}}>
            ${l(t.x,t.y)}
            <text x=${t.x} y=${t.y+23} text-anchor="middle">${_(r(e))}</text>
          </g>`})}
      </svg>`}let p,m,h=c&&a>1?260/(a-1):320,g=c&&h<90,_=c?Math.max(6,Math.floor((g?h*2:h)/7)):14,v=e=>e.length>_?`${e.slice(0,_-1)}…`:e;if(c){m=g?76:56;let t=g?38:18;p=e.map((e,n)=>({x:30+n*h,y:t}))}else m=134,p=e.map((e,t)=>{let n=-Math.PI/2+2*Math.PI*t/a;return{x:160+112*Math.cos(n),y:62+40*Math.sin(n)}});let y=e=>{let t=p[e];if(c)return{x:t.x,y:g&&e%2==1?t.y-15:t.y+24,anchor:`middle`};let n=t.y>=62;return{x:t.x,y:n?t.y+22:t.y-12,anchor:`middle`}};return F`<svg class="ov-diagram" viewBox="0 0 ${320} ${m}" role="img"
      aria-label=${e.map(r).join(`, `)}>
      ${o.map(([e,t])=>I`<line
        x1=${p[e].x} y1=${p[e].y} x2=${p[t].x} y2=${p[t].y}
        class="ov-line ${n}"></line>`)}
      ${e.map((e,t)=>{let n=y(t);return I`<g class="ov-node ${i(e)?`on`:``}" tabindex="0" role="button"
          aria-label=${r(e)}
          @click=${()=>this._openRoom(e)}
          @keydown=${t=>{(t.key===`Enter`||t.key===` `)&&(t.preventDefault(),this._openRoom(e))}}>
          ${l(p[t].x,p[t].y)}
          <text x=${n.x} y=${n.y} text-anchor=${n.anchor}>${v(r(e))}</text>
        </g>`})}
    </svg>`}_renderLateHome(){let e=this.hass.language,t=this._settings.late_home_persons??[];if(t.length===0)return L;let n=e=>Object.values(this.hass.states).find(t=>t.entity_id.startsWith(`switch.`)&&t.attributes.person===e);return F`
      <section class="late-home" aria-label=${V(`late.title`,e)}>
        <span class="late-title"><ha-icon icon="mdi:home-clock-outline"></ha-icon>${V(`late.title`,e)}</span>
        ${t.map(t=>{let r=n(t),i=this.hass.states[t]?.attributes.friendly_name??t,a=this.hass.states[t]?.state===`home`,o=r?.state===`on`;return F`<button
            class="late-btn ${o?`on`:``}"
            aria-pressed=${o?`true`:`false`}
            ?disabled=${!r||a&&!o}
            title=${r?a&&!o?V(`late.is_home`,e).replace(`{name}`,i):V(o?`late.on_hint`:`late.off_hint`,e):V(`late.restart`,e)}
            @click=${()=>r&&this.hass.callService(`switch`,o?`turn_off`:`turn_on`,{entity_id:r.entity_id})}
          >
            <ha-icon icon=${o?`mdi:home-clock`:a?`mdi:home-account`:`mdi:home-clock-outline`}></ha-icon>
            ${i}
            <span class="late-state">${V(o?`late.active`:a?`person.home`:`person.away`,e)}</span>
          </button>`})}
      </section>
    `}_linkList(){let e=this._config?.rooms??[];return[...tt(e,`linked_rooms`).map(e=>({kind:`motion`,group:e})),...tt(e,`fan_shared_rooms`).map(e=>({kind:`fan`,group:e}))].map((e,t)=>({...e,n:t+1}))}_renderOverview(e){let t=this.hass.language,n=this._settings.persons,r=new Map(e.map(e=>[e.area_id,ut(this.hass,e,n)])),i=e.filter(e=>r.get(e.area_id)?.status===`active`),a=e.filter(e=>!i.includes(e)),o=this._config?.rooms??[],s=e=>this.hass.areas?.[e]?.name??o.find(t=>t.area_id===e)?.name??e,c=e=>i.some(t=>t.area_id===e),l=e=>{let n=r.get(e.area_id)?.avg_brightness;return typeof n==`number`?`${Math.round(n/255*100)}%`:V(`card.on`,t)},u=this._linkList(),d=this._ovStacked&&u.length>0,f=F`
      <div class="ov-group" data-ov="active">
        <div class="ov-head">
          <span class="ov-dot ${i.length>0?`active`:``}"></span>
          <span class="ov-label">${V(`status.active`,t)}</span>
          <span class="ov-count">${i.length}</span>
        </div>
        ${i.length===0?F`<span class="ov-none">${V(`overview.none_on`,t)}</span>`:F`<div class="ov-rows">
              ${i.map(e=>F`
                <button class="ov-row" @click=${()=>this._openRoom(e.area_id)}>
                  <ha-icon icon="mdi:lightbulb-on"></ha-icon>
                  <span class="ov-row-name">${e.name}</span>
                  <span class="ov-row-val">${l(e)}</span>
                </button>`)}
            </div>`}
      </div>`,p=F`
      <div class="ov-group" data-ov="standby">
        <div class="ov-head">
          <span class="ov-dot"></span>
          <span class="ov-label">${V(`status.standby`,t)}</span>
          <span class="ov-count">${a.length}</span>
        </div>
        <div class="ov-chips">
          ${a.length===0?F`<span class="ov-none">—</span>`:a.map(e=>F`<button class="ov-chip" @click=${()=>this._openRoom(e.area_id)}>${e.name}</button>`)}
        </div>
      </div>`,m=u.length===0?L:F`
      <div class="ov-group ov-links" data-ov="links">
        <div class="ov-head">
          <ha-icon icon="mdi:link-variant" style="--mdc-icon-size:18px;color:var(--primary-color)"></ha-icon>
          <span class="ov-label">${V(`overview.linked`,t)}</span>
          <span class="ov-count">${u.length}</span>
        </div>
        ${u.map(({kind:e,group:n,n:r})=>{let i=nt(o,n,e===`motion`?`linked_rooms`:`fan_shared_rooms`),a=n.filter(c).length;return F`
            <div class="ov-link">
              <div class="ov-link-head">
                <span class="ov-kind ${e}">
                  <ha-icon icon=${e===`motion`?`mdi:link-variant`:`mdi:fan`}></ha-icon>
                  <strong>${r}</strong> · ${V(e===`motion`?`overview.kind_motion`:`overview.kind_fan`,t)}
                </span>
                <span class="ov-link-count">${a>0?V(`overview.n_on`,t).replace(`{n}`,String(a)):``}</span>
              </div>
              ${this._linkDiagram(i.order,i.direct,e,s,c)}
              ${i.via.length>0?F`<div class="ov-via">
                ${i.via.map(e=>F`<div>${V(`overview.via`,t).replace(`{a}`,s(e.a)).replace(`{b}`,s(e.b)).replace(`{through}`,e.through.map(s).join(`, `))}</div>`)}
              </div>`:L}
            </div>`})}
        <div class="ov-legend">
          <span><span class="ov-kind motion"><ha-icon icon="mdi:motion-sensor"></ha-icon>${V(`overview.kind_motion`,t)}</span> ${V(`overview.kind_motion_hint`,t)}</span>
          ${u.some(e=>e.kind===`fan`)?F`<span><span class="ov-kind fan"><ha-icon icon="mdi:fan"></ha-icon>${V(`overview.kind_fan`,t)}</span> ${V(`overview.kind_fan_hint`,t)}</span>`:L}
        </div>
      </div>`,h=e.length?Math.round(i.length/e.length*100):0;return F`
      <section class="overview-wrap" aria-label=${V(`overview.title`,t)}>
        <div class="ov-top">
          <span class="ov-title">${V(`overview.lit`,t).replace(`{n}`,String(i.length)).replace(`{total}`,String(e.length))}</span>
          ${u.length?F`<span class="ov-sub">${V(`overview.n_links`,t).replace(`{n}`,String(u.length))}</span>`:L}
        </div>
        <div class="ov-bar" role="presentation"><span style="width: ${h}%"></span></div>
        <div class="overview ${d?`stacked`:``}">
          ${d?F`<div class="ov-stack">${f}${p}</div>${m}`:F`${f}${p}${m}`}
        </div>
      </section>
    `}_renderGrouped(e,t){let n=this.hass.floors??{};if(!this._settings.group_by_floor||Object.keys(n).length===0)return t(e);let r=this.hass.language,i=new Map;for(let t of e){let e=this.hass.areas?.[t.area_id]?.floor_id,r=e&&n[e]?e:``;i.set(r,[...i.get(r)??[],t])}let a=Object.values(n).sort((e,t)=>(e.level??0)-(t.level??0)||e.name.localeCompare(t.name,r)).map(e=>e.floor_id).filter(e=>i.has(e));return i.has(``)&&a.push(``),a.map(e=>F`
        <h2 class="floor-title">
          <ha-icon icon=${e&&n[e].icon||`mdi:home-floor-1`}></ha-icon>
          ${e?n[e].name:V(`floors.none`,r)}
        </h2>
        ${t(i.get(e))}
      `)}async _setHidden(e,t){let n=this._config,r=this._withRoom({...e,hidden:t});this._config={...this._config,rooms:r};try{await Ie(this.hass,{rooms:r})}catch{this._config=n,this._error=V(`room.error_save`,this.hass.language)}}};q([z({attribute:!1})],$.prototype,`hass`,void 0),q([z({type:Boolean,reflect:!0})],$.prototype,`narrow`,void 0),q([z({type:Object})],$.prototype,`panel`,void 0),q([B()],$.prototype,`_config`,void 0),q([B()],$.prototype,`_loading`,void 0),q([B()],$.prototype,`_error`,void 0),q([B()],$.prototype,`_view`,void 0),q([B()],$.prototype,`_selectedAreaId`,void 0),q([B()],$.prototype,`_showHidden`,void 0),q([B()],$.prototype,`_settingsSave`,void 0),q([B()],$.prototype,`_dimBusy`,void 0),q([B()],$.prototype,`_ovStacked`,void 0),$=q([ke(`roomcontrol-panel`)],$);function hn(e){return(e.groups??[]).some(t=>{let n=Bt(e,t);return n.own_times?(n.slots??[]).some(e=>e.start.type!==`time`||e.end.type===`sunrise`):n.follow_schedule&&(e.schedules??[]).length>0})}