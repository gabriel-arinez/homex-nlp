import { chromium, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
const c=JSON.parse(fs.readFileSync('../live-final-config.json','utf8'))
const origin='http://127.0.0.1:'+c.frontport
const api='http://127.0.0.1:'+c.apiport
const results=[]
const browser=await chromium.launch({headless:true})
try {
 const context=await browser.newContext({baseURL:origin})
 await context.tracing.start({screenshots:true,snapshots:true,sources:false})
 const page=await context.newPage()
 page.setDefaultTimeout(20000)
 page.on('console',m=>console.log('BROWSER',m.type(),m.text()))
 page.on('pageerror',e=>console.log('PAGEERROR',String(e)))
 for(let n=0;n<40;n++){try{const r=await context.request.get(origin+'/login');if(r.ok())break}catch{} await new Promise(r=>setTimeout(r,500))}
 await page.goto('/login')
 await page.getByLabel('Usuario').fill(c.username)
 await page.getByLabel('Contraseña').fill(c.password)
 await page.getByRole('button',{name:'Ingresar',exact:true}).click()
 await page.waitForURL(u=>!u.pathname.endsWith('/login'))
 let headers={}
 // Capture only this newly generated synthetic login's request authorization.
 page.on('request',r=>{if(r.url().startsWith(api)&&r.headers().authorization) headers={authorization:r.headers().authorization}})
 await page.goto('/productos')
 await page.getByRole('group',{name:'Crear producto por categoría'}).waitFor()
 const inventory=async()=>{const r=await context.request.get(api+'/api/v1/catalogo/productos/',{headers});expect(r.status()).toBe(200);return await r.json()}
 const writes=[]
 page.on('request',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.method())&&/\/(catalogo\/productos|proformas|movimientos-stock)\//.test(r.url()))writes.push({method:r.method(),url:r.url()})})
 for(const id of ['MP-0004','MP-0062','MP-0067']){
  const record={id,category:'OTRO',status:'PENDING'}
  try {
   const before=await inventory()
   await page.goto('/productos/nuevo?categoria=OTRO')
   await page.getByRole('button',{name:'Completar por voz',exact:true}).click()
   const assistant=page.getByRole('dialog',{name:'Completar por voz',exact:true})
   const terminal=page.waitForResponse(async r=>{
    if(r.request().method()!=='GET'||r.status()!==200||!r.url().includes('/capturas/catalogo/'))return false
    const d=await r.json();return d.estado!=='PROCESANDO'&&d.estado!=='PENDIENTE'
   },{timeout:180000})
   const chooser=page.waitForEvent('filechooser')
   await assistant.getByRole('button',{name:'Seleccionar archivo'}).click()
   await(await chooser).setFiles(c.samples[id])
   record.response=await(await terminal).json()
   fs.writeFileSync(path.join(c.out,id+'-response.json'),JSON.stringify(record.response,null,2))
   console.log('REAL_RESPONSE',id,JSON.stringify(record.response))
   expect(record.response.estado).toBe('COMPLETADA')
   expect(record.response.categoria).toBe('OTRO')
   await assistant.waitFor({state:'hidden',timeout:15000})
   const fields=record.response.propuesta.fields
   const raw=record.response.texto_transcrito_original
   expect(fields.nombre?.length).toBeGreaterThan(8)
   expect(fields.nombre).toMatch(/poltronas?\s+fijas?/i)
   expect(raw.startsWith(fields.nombre)).toBe(true)
   if(id==='MP-0004'||id==='MP-0062')expect(fields.nombre).toMatch(/^2 poltronas fijas/i)
   expect(fields.observaciones).toBe(raw)
   expect(Number(fields.precio_lista)).toBe(5500)
   for(const key of Object.keys(fields))expect(['nombre','observaciones','precio_lista','unidad_stock']).toContain(key)
   expect(await page.getByLabel('Nombre comercial *',{exact:false}).inputValue()).toBe(fields.nombre)
   expect(await page.getByLabel('Notas del producto (opcional)').inputValue()).toBe(raw)
   expect(Number(await page.getByLabel('Precio normal de venta (Bs) *',{exact:false}).inputValue())).toBe(5500)
   expect(writes).toEqual([])
   expect(await inventory()).toEqual(before)
   record.fields=fields
   record.inventoryBefore=before
   record.inventoryUnchanged=true
   record.commercialWrites=[...writes]
   record.status='PASS'
  }catch(e){record.status='FAIL';record.error=String(e);console.log('PROBE_FAILURE',id,String(e))}
  await page.screenshot({path:path.join(c.out,id+'.png'),fullPage:true})
  results.push(record)
  fs.writeFileSync(path.join(c.out,'results.json'),JSON.stringify(results,null,2))
  console.log('CATEGORY_RESULT',id,record.status)
 }
 await context.tracing.stop({path:path.join(c.out,'trace.zip')})
 await context.close()
}finally{await browser.close()}
console.log('FINAL_RESULTS',JSON.stringify(results.map(({id,category,status,error})=>({id,category,status,error}))))
process.exitCode=results.length===3&&results.every(r=>r.status==='PASS')?0:1
