BEGIN;

CREATE OR REPLACE FUNCTION pg_temp.cv(c text,v text) RETURNS bigint LANGUAGE SQL AS $$ SELECT a.id FROM catalogo_valores a JOIN catalogo_conceptos b ON b.id=a.concepto_id WHERE b.codigo=c AND a.codigo=v $$;
INSERT INTO clientes(id,tipo_cliente_id,nombres,apellidos) VALUES(90001,pg_temp.cv('TIPO_CLIENTE','PERSONA'),'Prueba','Auditoria');
INSERT INTO productos(id,categoria_id,nombre,unidad_stock_id) VALUES(90001,pg_temp.cv('CATEGORIA_PRODUCTO','OTRO'),'Producto prueba',pg_temp.cv('UNIDAD_MEDIDA','PIEZA'));
INSERT INTO movimientos_stock(producto_id,tipo_movimiento_id,cantidad) VALUES(90001,pg_temp.cv('TIPO_MOVIMIENTO','CARGA_INICIAL'),10);
INSERT INTO proformas(id,numero,cliente_id,vendedor_id,estado_id,moneda_id) VALUES(90001,90001,90001,1,pg_temp.cv('ESTADO_PROFORMA','BORRADOR'),pg_temp.cv('MONEDA','BOB')),(90002,90002,90001,1,pg_temp.cv('ESTADO_PROFORMA','BORRADOR'),pg_temp.cv('MONEDA','BOB'));
INSERT INTO proformas_detalle(id,proforma_id,tipo_item_id,producto_id,nombre,cantidad,unidad_id,precio_unitario) VALUES(90001,90001,pg_temp.cv('TIPO_ITEM','OTRO'),90001,'Producto prueba',2,pg_temp.cv('UNIDAD_MEDIDA','PIEZA'),100);

INSERT INTO productos(id,categoria_id,nombre,unidad_stock_id) VALUES(90002,pg_temp.cv('CATEGORIA_PRODUCTO','SILLA'),'Silla prueba',pg_temp.cv('UNIDAD_MEDIDA','PIEZA')); INSERT INTO productos_silla(producto_id) VALUES(90002); UPDATE productos SET categoria_id=pg_temp.cv('CATEGORIA_PRODUCTO','OTRO') WHERE id=90002; DO $$ BEGIN ASSERT EXISTS(SELECT 1 FROM productos_silla WHERE producto_id=90002); RAISE NOTICE 'VERIFICADO'; END $$;
SELECT 'AUDIT_OK';
ROLLBACK;
