# LogCash
#### Video Demo:  https://youtu.be/dYflH7b5DnE
#### Description: 

I started this project thinking about my friends' company, how they are never properly organized
with their spending, and they never know how much money they are spending and where it can be cut so
I went out to make an web app that could organize a person's spending, displaying separately their
personal spending but also their company's spending, so solo entrepeneurs can know why they are in the
red and how they can improve it.

At the start I had in mind one thing, the UI needed to be user-friendly, so I searched all around
the internet for something like bootstrap but more modern and mobile-like, because I needed my app to
work both on desktop and mobile modes, I ended up picking DaisyUI, but that meant learning my way around
both it and TailwindCSS which proved to be quite a challenge.

UI work kept going alongside the crafting of a proper database to store these expenses, I ended up
trimming it down to 3 tables, a users table, a categorias table where the categories of expenses are stored
for display in the webpage and ease of adding new categiories in the future, and a despesas table where
all the expenses are laid out and organized for proper display in the page.
    The website is built for portuguese speakers, more specifically brazilian portuguese, and is using
Flask as its framework, alongside tailwindcss for the UI, the programming languages included in the project
are Python and JavaScript, with HTML and CSS as markup languages.

The user starts off registering in the webpage, where they need to fill the username, password, confirm
the password and write their e-mail, all with proper error handling through javascript, which is my least
known language so I ended up trying a new approach in the future for error handling in the future pages,
but it works well enough for this register/login routes, the login page works similarly, hashing the password
as we learned in the Flask class.

The Geral (index) page greets a new user empty, we will go back to it as soon as we input some data into the app.

The Pessoal page is where we add expenses for the individual (not the company), the categories are more
specific for this kind of expense, there are 2 categories where the user can input their expense, Fixa, where
their expense is like a subscription and will keep happening in future months unless deleted, or Variavel,
where it is a regular expense like going to the supermarket or buying some clothes, the user then adds that
expense with the Adicionar button and it refreshes the page, displaying the expense in a table below the input
while also updating the full Despesa Fixa/Variavel boxes at the top with the new expense, in the table I
have placed a button to the right where the user can Delete that expense, which also updates the page so
it is gone.

The Empresa page works similarly to the Pessoal page, but it's about the company instead and has categories
that are relevant to the users' business.

Now going back to the Geral (index) page, where the expenses are now displayed with a box for each month
containing the total expenses in that month for the company and the individual, with a separated Total expenses
display, so the user can know how much he spent that month, the months are displayed in a user friendly way,
using portuguese language like Dezembro 2024, Novembro 2024, etc. All of these boxes are actually buttons, so
if the user clicks on one of them they can display all the expenses of that month, including previous monthly
expenses in a zebra styled table.

The user can also log out, which clears the cache for a new login or register action.
    
The most challenging aspects of this project was learning my way around Flask properly, understanding that
I needed to create new routes for different processes, especially for error handling using Flash, which ended
up being my default error handling for the rest of the project given I got more comfortable with Python than
with Javascript and I was more confident I could make a more streamlined experience that way. Other challenge
I had was dealing with the sqlite database, I had to make some very specific queries and process the data in
my app.py so I could have the monthly expenses from previous months be displayed in the following months.
    A part of the work of this project was talking to my "client" and learning what categories they thought
were important for both their personal and company expenses, so I made the website very flexible with a simple
INSERT to my categorias database I could add a new category for my client if they were in need.
