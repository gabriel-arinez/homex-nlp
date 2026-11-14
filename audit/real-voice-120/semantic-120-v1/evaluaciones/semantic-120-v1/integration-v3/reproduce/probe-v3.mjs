import { chromium, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
const c=JSON.parse(fs.readFileSync(process.env.HOMEX_REPRO_CONFIG,'utf8'))
const origin='http://127.0.0.1:'+c.frontport
const api='http://127.0.0.1:'+c.apiport
const results=[]
const browser=await chromium.launch({headless:true})
try {
 const context=await browser.newContext({baseURL:origin})
 await context.tracing.start({screenshots:true,snapshots:true,sources:false})
 let page=await context.newPage(); page.setDefaultTimeout(20000)
 page.on('console',m=>console.log('BROWSER',m.type(),m.text()))
 page.on('pageerror',e=>console.log('PAGEERROR',String(e)))
 for(let n=0;n<40;n++){try{const r=await context.request.get(origin+'/login');if(r.ok())break}catch{} await new Promise(r=>setTimeout(r,500))}
 await page.goto('/login')
 await page.getByLabel('Usuario').fill(c.username)
 await page.getByLabel('Contraseña').fill(c.password)
 await page.getByRole('button',{name:'Ingresar',exact:true}).click()
 await page.waitForURL(u=>!u.pathname.endsWith('/login'))
 // Reuse only the just-created synthetic browser session, never ambient tokens.
 let headers={}
 context.on('request',r=>{if(r.url().startsWith(api)&&r.headers().authorization) headers={authorization:r.headers().authorization}})
 await page.goto('/productos')
 await page.getByRole('group',{name:'Crear producto por categoría'}).waitFor()
 const inventory=async()=>{const r=await context.request.get(api+'/api/v1/catalogo/productos/',{headers});expect(r.status()).toBe(200);return await r.json()}
 const writes=[]
 context.on('request',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.method())&&/\/(catalogo\/productos|proformas|movimientos-stock)\//.test(r.url()))writes.push({method:r.method(),url:r.url()})})
 for (const [id,category] of [['MP-0001','MUEBLE'],['SIL-0001','SILLA'],['PIS-0001','PISO_FLOTANTE'],['MP-0005','OTRO'],['MP-0036','MUEBLE'],['MP-0045','MUEBLE'],['MP-0067','OTRO'],['PIS-0006','PISO_FLOTANTE']]){
  await page.close(); page=await context.newPage(); page.setDefaultTimeout(20000);
  await page.goto('/login');
  await page.getByLabel('Usuario').fill(c.username);
  await page.getByLabel('Contraseña').fill(c.password);
  await page.getByRole('button',{name:'Ingresar',exact:true}).click();
  await page.waitForURL(u=>!u.pathname.endsWith('/login'));
  const startedAt=Date.now(); const record={id,category,status:'PENDING'}
  try {
   const before=await inventory()
   if(category==='MUEBLE'){
    await page.goto('/proformas/nueva')
    await page.getByRole('button',{name:'Añadir ítem'}).click()
    await page.getByRole('button',{name:/^Mueble a pedido/}).click()
   }else{
    await page.goto('/productos/nuevo?categoria='+category)
   }
   await page.getByRole('button',{name:'Completar por voz',exact:true}).click()
   const assistant=page.getByRole('dialog',{name:category==='MUEBLE'?'Completar mueble por voz':'Completar por voz',exact:true})
   const terminal=page.waitForResponse(async r=>{
    if(r.request().method()!=='GET'||r.status()!==200||!r.url().includes(category==='MUEBLE'?'/capturas/asistidas/':'/capturas/catalogo/'))return false
    const d=await r.json();return category==='MUEBLE'?d.resultado!=='PROCESSING':d.estado!=='PROCESANDO'&&d.estado!=='PENDIENTE'
   },{timeout:180000})
   const chooser=page.waitForEvent('filechooser')
   await assistant.getByRole('button',{name:'Seleccionar archivo'}).click()
   await(await chooser).setFiles(c.samples[id])
   const response=await terminal
   record.response=await response.json()
   fs.writeFileSync(path.join(c.out,id+'-response.json'),JSON.stringify(record.response,null,2))
   console.log('REAL_RESPONSE',id,JSON.stringify(record.response))
   if(category==='MUEBLE'){
    expect(record.response.resultado).toBe('REQUIRES_REVIEW')
    expect(record.response.propuesta_configurador).toBeTruthy()
    // Existing studio applies the reviewed proposal when the drawer closes.
    await assistant.waitFor({state:'hidden',timeout:15000})
    await page.getByRole('navigation',{name:'Apartados del mueble a pedido'}).getByRole('button',{name:/General/}).click()
    record.generalInputs=await page.locator('input').evaluateAll(xs=>xs.map(x=>({name:x.name,value:x.value})))
    expect(await page.getByLabel('Nombre comercial del mueble').inputValue()).not.toBe('')
    record.proposal=record.response.propuesta_configurador;
    expect(await page.getByLabel('Nombre comercial del mueble').inputValue()).toBe(record.proposal.comercial.nombre);
    const mappedDims=record.proposal.especificacion.datos_tecnicos.caracteristicas_generales?.dimensiones ?? {};
    for(const [axis,dim] of Object.entries(mappedDims)) {
      expect(Number(await page.locator('input[name="'+axis+'"]').inputValue())).toBe(Number(dim.valor));
      expect(await page.getByLabel('Unidad de '+axis,{exact:true}).inputValue()).toBe(dim.unidad);
    }
    record.mappedDimensions=mappedDims;
    await page.getByRole('navigation',{name:'Apartados del mueble a pedido'}).getByRole('button',{name:/Precio/}).click();
    expect(Number(await page.getByLabel('Cantidad cotizada').inputValue())).toBe(Number(record.proposal.comercial.cantidad));
    if(record.proposal.comercial.precio_unitario)expect(Number(await page.getByLabel('Precio unitario negociado (BOB)').inputValue())).toBe(Number(record.proposal.comercial.precio_unitario));
    if(id==='MP-0001'){
      expect(Number(mappedDims.diametro.valor)).toBe(2);expect(mappedDims.diametro.unidad).toBe('m');
      expect(Number(mappedDims.alto.valor)).toBe(75);expect(mappedDims.alto.unidad).toBe('cm');
      expect(Number(record.proposal.comercial.cantidad)).toBe(2);
      expect(Number(record.proposal.comercial.precio_unitario)).toBe(7300);
    }
   }else{
    expect(record.response.estado).toBe('COMPLETADA')
    await assistant.waitFor({state:'hidden',timeout:15000})
    const fields=record.response.propuesta.fields
    record.fields=fields; record.evidenceRetained=Array.isArray(record.response.propuesta.evidence); record.warnings=record.response.propuesta.warnings; for(const e of record.response.propuesta.evidence??[])expect(record.response.texto_transcrito_original.slice(e.start,e.end)).toBe(e.text); expect(record.evidenceRetained).toBe(true); if(fields.modelo)expect(await page.getByLabel('Modelo',{exact:true}).inputValue()).toBe(String(fields.modelo));
    if(fields.nombre)expect(await page.getByLabel('Nombre comercial *',{exact:false}).inputValue()).toBe(String(fields.nombre))
    const expectedPrice={SILLA:5200,PISO_FLOTANTE:125,OTRO:12000}[category]
    if(['SIL-0001','PIS-0001','MP-0005'].includes(id))expect(Number(fields.precio_lista)).toBe(expectedPrice)
    expect(Number(await page.getByLabel('Precio normal de venta (Bs) *',{exact:false}).inputValue())).toBe(Number(fields.precio_lista))
    if(category==='PISO_FLOTANTE'){
     expect(Number(fields.espesor_mm)).toBe(8)
     if(fields.espesor_mm !== undefined)expect(Number(await page.getByLabel('Espesor (mm)',{exact:false}).inputValue())).toBe(Number(fields.espesor_mm)); else { expect(await page.getByLabel('Espesor (mm)',{exact:false}).inputValue()).toBe(''); record.limitations=['Thickness omitted by NLP; no fabricated value applied']; }
    }
    if(category==='OTRO'){
     expect(fields.observaciones?.length).toBeGreaterThan(20)
     expect(await page.getByLabel('Notas del producto (opcional)').inputValue()).toBe(fields.observaciones)
     expect(fields).not.toHaveProperty('especificaciones')
     expect(fields).not.toHaveProperty('espesor_mm')
    }
   }
   expect(writes).toEqual([])
   expect(await inventory()).toEqual(before)
   record.inventoryUnchanged=true
   record.status='PASS'
  }catch(e){record.status='FAIL';record.error=String(e);console.log('PROBE_FAILURE',id,String(e))}
  record.elapsedMs=Date.now()-startedAt; record.latencyInterpretation='Diagnostic under concurrent CPU ASR workload; not a benchmark'; await page.screenshot({path:path.join(c.out,id+'.png'),fullPage:true})
  results.push(record)
  fs.writeFileSync(path.join(c.out,'results.json'),JSON.stringify(results,null,2))
  console.log('CATEGORY_RESULT',id,record.status)
 }
 await context.tracing.stop({path:path.join(c.out,'trace.zip')})
 await context.close()
}finally{await browser.close()}
console.log('FINAL_RESULTS',JSON.stringify(results.map(({id,category,status,error})=>({id,category,status,error}))))
process.exitCode=results.length===8&&results.every(r=>r.status==='PASS')?0:1
