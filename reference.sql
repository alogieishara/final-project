INSERT INTO categorias (categoria, escopo, tipo) VALUES ('Papelaria', 'empresa', 'variavel'), ('Mercado', 'empresa', 'variavel'), ('Ferramenta', 'empresa', 'variavel'), ('Terceirizado', 'empresa', 'variavel');

SELECT *
FROM purchases
WHERE strftime('%Y-%m', time) = '2024-09';