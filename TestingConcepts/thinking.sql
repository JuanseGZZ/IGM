select * from products p
join product_attribute_values pav
on (pav.product_id = p.id)

select * from attributes where id = 1

select *
from products p
join product_attribute_values pav
    on pav.product_id = p.id
where category_id = 1 and 
attribute_id = (select id from attributes where key = 'peso_g')
and (pav.value ->> 'number')::numeric < 300;