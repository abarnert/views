# views
Lazy views for zip, filter, etc.

When Swift first came out, [I was impressed][1] by its [collection design][2]. In particular, the `map` and `filter` functions returned view objects, which were lazy (like Python 3), but also as full-featured a possible. In Python terms, rather than being just iterators, a `map` view is a sequence if its input is, falling back to a bidirectional collection, a forward-only collection, and a one-shot iterator as its input does, while a `filter` view is a bidirectional collection, forward-only collection, or one-shot iterator.

As it turns out, the way Swift implemented iterables and iterators (because of a limitation in the beta language's type system) means `map` and `filter` don't really work on iterators. And even in Swift 2.1, the type system makes it very hard to factor out the commonalities and generate a set of view classes for each higher-order function without duplicating a whole mess of code. And of course writing n-ary `map`, `zip`, etc. in a statically-typed language without a really amazing type system (better than Swift's) is a huge pain.

Meanwhile, I realized that you don't actually need the complicated idea of generalized indexes to make this design work. All Python was missing was a [`Reversible`][3] ABC, and you can easily and readably express everything needed, from "if the input is a sequence" to "reverse-iterate this by reverse-iterating all of the inputs with extra fill values chained on the end". The key insight I'd missed at first was taking `Sized` into account--e.g., `zip` is only reversible if its inputs are sized as well as reversible (unless there's only one iterable). There's a bit more complexity when you look at filling the gaps between `islice` and native slices (when are negative numbers allowed? etc.), but nothing you can't figure out with a couple minutes of thought.

So, I decided to implement a half dozen useful and diverse functions as lazy views, make sure there aren't any unanticipated problems, and then look at how to refactor things so that writing a new such function is almost as easy (or at least within an order of magnitude...) as writing a new iterator-only version.

Functions
=========

 * `map(func, iterable, *iterables)`: sequence, sized reversible, reversible, or iterable
 * `filter(func, iterable)`: reversible or iterable
 * `zip(*iterables)`: sequence, sized reversible, or iterable
 * `zip_longest(*iterables, fillvalue)`: sequence, sized reversible, or iterable
 * `enumerate(iterable, start)`: sequence, sized reversible, or iterable
 * `islice(iterable, start[, stop[, step]])`: sequence, 

The last fallback, "iterable", is actually two different possibilities--if given an iterator, all of these types produce an iterator, but if given a reusable iterable, they produce a reusable iterable. And that just happens automagically, unlike the LBYL "try sequence, fall back" stuff. (In theory, "reversible", or even "sized reversible", could be iterators too, but that's very unlikely, and would imply some very odd types; in practice, only the last fallback, "iterable", may be an iterator.

Future plans
============

* Add real unit tests and fix bugs.
* Look for commonalities in the code and figure out how to refactor them (that being the main point of this exercise).
* More functions (to test the refactoring).
* Maybe clean up the the library and put it on PyPI?

For the last one, I'm not sure how useful this would be, unless the views are used pervasively. I can shadow the builtins with `from views import *`, but that isn't going to make `a[:-3]` return a view unless `a` is already a view (unless I write an import hook for that...), nor is it going to give me a way to write a view-based lazy comprehension. But we'll see.

  [1]: http://stupidpythonideas.blogspot.com/2014/07/swift-style-map-and-filter-views.html
  [2]: https://github.com/apple/swift/blob/master/docs/SequencesAndCollections.rst
  [3]: http://bugs.python.org/issue25987
