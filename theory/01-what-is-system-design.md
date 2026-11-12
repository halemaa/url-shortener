# 1. What system design is

## Algorithms have answers. Designs have trade-offs.

An algorithm question has a correct answer: the merge either produces
a sorted list or it doesn't.

A system design question does not. "How should we store these links?"
has several reasonable answers, and each one costs something. The
skill is choosing one and being able to say what you gave up.

## A recipe versus a restaurant

A recipe is an algorithm. Follow the steps and you get the dish.

Running a restaurant is system design:

- How many tables, and how many cooks?
- What happens when fifty people arrive at once?
- What happens when the fridge breaks?
- What do you keep ready on the counter, and what stays in the store?

Nobody can say "the correct number of tables is 14." It depends on the
rent, the menu, and how many people come.

## The questions every design has to answer

1. **What does it do?** List the operations. For a URL shortener:
   create a short link, and follow one.
2. **How much?** How many requests, how much data, how fast must it be.
3. **Where does the data live?** And what happens to it on a restart.
4. **What is the common case?** Make that fast. Here, following a link
   happens far more often than creating one.
5. **What goes wrong?** Clashes, abuse, a machine going down.
6. **What breaks first when it grows?** And what you would change.

## Why a URL shortener is the standard exercise

It is small enough to understand in a minute and still touches every
question above: generating identifiers, storage, caching, abuse, and
growth. That is why it is one of the most common interview questions.

## The word to listen for: "because"

A design answer without "because" is a guess.

- Weak: "I'd use a cache."
- Strong: "I'd cache lookups because links are read far more often
  than they are created, and a link never changes once it exists, so
  the cached copy can't go stale."

Every record in the `design/` folder is written in that shape:
the options, the choice, why, and what it costs.
