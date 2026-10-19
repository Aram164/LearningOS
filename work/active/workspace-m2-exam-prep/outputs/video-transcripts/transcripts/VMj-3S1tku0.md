---
video_id: VMj-3S1tku0
url: https://www.youtube.com/watch?v=VMj-3S1tku0
title: The spelled-out intro to neural networks and backpropagation: building micrograd
channel: Andrej Karpathy
duration: 145:52
language: en
unit: L15
status: OK
---

[00:00] hello my name is andre and i've been training deep neural
[00:02] and i've been training deep neural networks for a bit more than a decade
[00:04] networks for a bit more than a decade and in this lecture i'd like to show you
[00:06] and in this lecture i'd like to show you what neural network training looks like
[00:08] what neural network training looks like under the hood so in particular we are
[00:10] under the hood so in particular we are going to start with a blank jupiter
[00:12] going to start with a blank jupiter notebook and by the end of this lecture
[00:14] notebook and by the end of this lecture we will define and train in neural net
[00:16] we will define and train in neural net and you'll get to see everything that
[00:18] and you'll get to see everything that goes on under the hood and exactly
[00:20] goes on under the hood and exactly sort of how that works on an intuitive
[00:21] sort of how that works on an intuitive level
[00:22] level now specifically what i would like to do
[00:24] now specifically what i would like to do is i would like to take you through
[00:26] is i would like to take you through building of micrograd now micrograd is
[00:29] building of micrograd now micrograd is this library that i released on github
[00:30] this library that i released on github about two years ago but at the time i
[00:32] about two years ago but at the time i only uploaded the source code and you'd
[00:34] only uploaded the source code and you'd have to go in by yourself and really
[00:37] have to go in by yourself and really figure out how it works
[00:39] figure out how it works so in this lecture i will take you
[00:40] so in this lecture i will take you through it step by step and kind of
[00:42] through it step by step and kind of comment on all the pieces of it so what
[00:44] comment on all the pieces of it so what is micrograd and why is it interesting
[00:47] is micrograd and why is it interesting good
[00:48] good um
[00:49] um micrograd is basically an autograd
[00:51] micrograd is basically an autograd engine autograd is short for automatic
[00:53] engine autograd is short for automatic gradient and really what it does is it
[00:55] gradient and really what it does is it implements backpropagation now
[00:57] implements backpropagation now backpropagation is this algorithm that
[00:59] backpropagation is this algorithm that allows you to efficiently evaluate the
[01:01] allows you to efficiently evaluate the gradient of
[01:03] gradient of some kind of a loss function with
[01:05] some kind of a loss function with respect to the weights of a neural
[01:07] respect to the weights of a neural network and what that allows us to do
[01:09] network and what that allows us to do then is we can iteratively tune the
[01:11] then is we can iteratively tune the weights of that neural network to
[01:12] weights of that neural network to minimize the loss function and therefore
[01:14] minimize the loss function and therefore improve the accuracy of the network so
[01:16] improve the accuracy of the network so back propagation would be at the
[01:18] back propagation would be at the mathematical core of any modern deep
[01:20] mathematical core of any modern deep neural network library like say pytorch
[01:22] neural network library like say pytorch or jaxx
[01:24] or jaxx so the functionality of microgrant is i
[01:25] so the functionality of microgrant is i think best illustrated by an example so
[01:27] think best illustrated by an example so if we just scroll down here
[01:29] if we just scroll down here you'll see that micrograph basically
[01:31] you'll see that micrograph basically allows you to build out mathematical
[01:32] allows you to build out mathematical expressions
[01:34] expressions and um here what we are doing is we have
[01:36] and um here what we are doing is we have an expression that we're building out
[01:37] an expression that we're building out where you have two inputs a and b
[01:40] where you have two inputs a and b and you'll see that a and b are negative
[01:43] and you'll see that a and b are negative four and two but we are wrapping those
[01:46] four and two but we are wrapping those values into this value object that we
[01:48] values into this value object that we are going to build out as part of
[01:49] are going to build out as part of micrograd
[01:51] micrograd so this value object will wrap the
[01:53] so this value object will wrap the numbers themselves
[01:54] numbers themselves and then we are going to build out a
[01:56] and then we are going to build out a mathematical expression here where a and
[01:58] mathematical expression here where a and b are transformed into c d and
[02:01] b are transformed into c d and eventually e f and g
[02:03] eventually e f and g and i'm showing some of the functions
[02:05] and i'm showing some of the functions some of the functionality of micrograph
[02:07] some of the functionality of micrograph and the operations that it supports so
[02:08] and the operations that it supports so you can add two value objects you can
[02:11] you can add two value objects you can multiply them you can raise them to a
[02:13] multiply them you can raise them to a constant power you can offset by one
[02:15] constant power you can offset by one negate squash at zero
[02:18] negate squash at zero square divide by constant divide by it
[02:21] square divide by constant divide by it etc
[02:22] etc and so we're building out an expression
[02:24] and so we're building out an expression graph with with these two inputs a and b
[02:27] graph with with these two inputs a and b and we're creating an output value of g
[02:30] and we're creating an output value of g and micrograd will in the background
[02:32] and micrograd will in the background build out this entire mathematical
[02:34] build out this entire mathematical expression so it will for example know
[02:36] expression so it will for example know that c is also a value
[02:38] that c is also a value c was a result of an addition operation
[02:41] c was a result of an addition operation and the
[02:42] and the child nodes of c are a and b because the
[02:46] child nodes of c are a and b because the and will maintain pointers to a and b
[02:48] and will maintain pointers to a and b value objects so we'll basically know
[02:50] value objects so we'll basically know exactly how all of this is laid out
[02:53] exactly how all of this is laid out and then not only can we do what we call
[02:55] and then not only can we do what we call the forward pass where we actually look
[02:57] the forward pass where we actually look at the value of g of course that's
[02:58] at the value of g of course that's pretty straightforward we will access
[03:00] pretty straightforward we will access that using the dot data attribute and so
[03:03] that using the dot data attribute and so the output of the forward pass the value
[03:06] the output of the forward pass the value of g is 24.7 it turns out but the big
[03:09] of g is 24.7 it turns out but the big deal is that we can also take this g
[03:11] deal is that we can also take this g value object and we can call that
[03:13] value object and we can call that backward
[03:14] backward and this will basically uh initialize
[03:16] and this will basically uh initialize back propagation at the node g
[03:19] back propagation at the node g and what backpropagation is going to do
[03:21] and what backpropagation is going to do is it's going to start at g and it's
[03:23] is it's going to start at g and it's going to go backwards through that
[03:25] going to go backwards through that expression graph and it's going to
[03:26] expression graph and it's going to recursively apply the chain rule from
[03:28] recursively apply the chain rule from calculus
[03:30] calculus and what that allows us to do then is
[03:32] and what that allows us to do then is we're going to evaluate basically the
[03:34] we're going to evaluate basically the derivative of g with respect to all the
[03:36] derivative of g with respect to all the internal nodes
[03:38] internal nodes like e d and c but also with respect to
[03:40] like e d and c but also with respect to the inputs a and b
[03:43] the inputs a and b and then we can actually query this
[03:45] and then we can actually query this derivative of g with respect to a for
[03:47] derivative of g with respect to a for example that's a dot grad in this case
[03:50] example that's a dot grad in this case it happens to be 138 and the derivative
[03:52] it happens to be 138 and the derivative of g with respect to b
[03:54] of g with respect to b which also happens to be here 645
[03:57] which also happens to be here 645 and this derivative we'll see soon is
[03:59] and this derivative we'll see soon is very important information because it's
[04:01] very important information because it's telling us how a and b are affecting g
[04:04] telling us how a and b are affecting g through this mathematical expression so
[04:06] through this mathematical expression so in particular
[04:08] in particular a dot grad is 138 so if we slightly
[04:11] a dot grad is 138 so if we slightly nudge a and make it slightly larger
[04:14] nudge a and make it slightly larger 138 is telling us that g will grow and
[04:17] 138 is telling us that g will grow and the slope of that growth is going to be
[04:19] the slope of that growth is going to be 138
[04:20] 138 and the slope of growth of b is going to
[04:22] and the slope of growth of b is going to be 645. so that's going to tell us about
[04:25] be 645. so that's going to tell us about how g will respond if a and b get
[04:27] how g will respond if a and b get tweaked a tiny amount in a positive
[04:29] tweaked a tiny amount in a positive direction
[04:31] direction okay
[04:33] now you might be confused about what this expression is that we built out
[04:36] this expression is that we built out here and this expression by the way is
[04:38] here and this expression by the way is completely meaningless i just made it up
[04:40] completely meaningless i just made it up i'm just flexing about the kinds of
[04:42] i'm just flexing about the kinds of operations that are supported by
[04:43] operations that are supported by micrograd
[04:44] micrograd what we actually really care about are
[04:46] what we actually really care about are neural networks but it turns out that
[04:48] neural networks but it turns out that neural networks are just mathematical
[04:49] neural networks are just mathematical expressions just like this one but
[04:51] expressions just like this one but actually slightly bit less crazy even
[04:54] actually slightly bit less crazy even neural networks are just a mathematical
[04:56] neural networks are just a mathematical expression they take the input data as
[04:59] expression they take the input data as an input and they take the weights of a
[05:00] an input and they take the weights of a neural network as an input and it's a
[05:02] neural network as an input and it's a mathematical expression and the output
[05:04] mathematical expression and the output are your predictions of your neural net
[05:06] are your predictions of your neural net or the loss function we'll see this in a
[05:08] or the loss function we'll see this in a bit but basically neural networks just
[05:10] bit but basically neural networks just happen to be a certain class of
[05:12] happen to be a certain class of mathematical expressions
[05:13] mathematical expressions but back propagation is actually
[05:15] but back propagation is actually significantly more general it doesn't
[05:17] significantly more general it doesn't actually care about neural networks at
[05:18] actually care about neural networks at all it only tells us about arbitrary
[05:20] all it only tells us about arbitrary mathematical expressions and then we
[05:22] mathematical expressions and then we happen to use that machinery for
[05:24] happen to use that machinery for training of neural networks now one more
[05:26] training of neural networks now one more note i would like to make at this stage
[05:28] note i would like to make at this stage is that as you see here micrograd is a
[05:30] is that as you see here micrograd is a scalar valued auto grant engine so it's
[05:32] scalar valued auto grant engine so it's working on the you know level of
[05:34] working on the you know level of individual scalars like negative four
[05:36] individual scalars like negative four and two and we're taking neural nets and
[05:37] and two and we're taking neural nets and we're breaking them down all the way to
[05:39] we're breaking them down all the way to these atoms of individual scalars and
[05:41] these atoms of individual scalars and all the little pluses and times and it's
[05:43] all the little pluses and times and it's just excessive and so obviously you
[05:45] just excessive and so obviously you would never be doing any of this in
[05:47] would never be doing any of this in production it's really just put down for
[05:48] production it's really just put down for pedagogical reasons because it allows us
[05:50] pedagogical reasons because it allows us to not have to deal with these
[05:52] to not have to deal with these n-dimensional tensors that you would use
[05:54] n-dimensional tensors that you would use in modern deep neural network library so
[05:56] in modern deep neural network library so this is really done so that you
[05:58] this is really done so that you understand and refactor out back
[06:00] understand and refactor out back propagation and chain rule and
[06:02] propagation and chain rule and understanding of neurologic training
[06:04] understanding of neurologic training and then if you actually want to train
[06:06] and then if you actually want to train bigger networks you have to be using
[06:08] bigger networks you have to be using these tensors but none of the math
[06:09] these tensors but none of the math changes this is done purely for
[06:11] changes this is done purely for efficiency we are basically taking scale
[06:13] efficiency we are basically taking scale value
[06:14] value all the scale values we're packaging
[06:16] all the scale values we're packaging them up into tensors which are just
[06:17] them up into tensors which are just arrays of these scalars and then because
[06:20] arrays of these scalars and then because we have these large arrays we're making
[06:22] we have these large arrays we're making operations on those large arrays that
[06:24] operations on those large arrays that allows us to take advantage of the
[06:26] allows us to take advantage of the parallelism in a computer and all those
[06:28] parallelism in a computer and all those operations can be done in parallel and
[06:30] operations can be done in parallel and then the whole thing runs faster but
[06:32] then the whole thing runs faster but really none of the math changes and
[06:33] really none of the math changes and that's done purely for efficiency so i
[06:35] that's done purely for efficiency so i don't think that it's pedagogically
[06:36] don't think that it's pedagogically useful to be dealing with tensors from
[06:38] useful to be dealing with tensors from scratch uh and i think and that's why i
[06:40] scratch uh and i think and that's why i fundamentally wrote micrograd because
[06:42] fundamentally wrote micrograd because you can understand how things work uh at
[06:44] you can understand how things work uh at the fundamental level and then you can
[06:46] the fundamental level and then you can speed it up later okay so here's the fun
[06:48] speed it up later okay so here's the fun part my claim is that micrograd is what
[06:51] part my claim is that micrograd is what you need to train your networks and
[06:52] you need to train your networks and everything else is just efficiency so
[06:54] everything else is just efficiency so you'd think that micrograd would be a
[06:56] you'd think that micrograd would be a very complex piece of code and that
[06:58] very complex piece of code and that turns out to not be the case
[07:01] turns out to not be the case so if we just go to micrograd
[07:03] so if we just go to micrograd and you'll see that there's only two
[07:05] and you'll see that there's only two files here in micrograd this is the
[07:07] files here in micrograd this is the actual engine it doesn't know anything
[07:09] actual engine it doesn't know anything about neural nuts and this is the entire
[07:10] about neural nuts and this is the entire neural nets library
[07:12] neural nets library on top of micrograd so engine and nn.pi
[07:17] on top of micrograd so engine and nn.pi so the actual backpropagation autograd
[07:19] so the actual backpropagation autograd engine
[07:21] engine that gives you the power of neural
[07:22] that gives you the power of neural networks is literally
[07:26] networks is literally 100 lines of code of like very simple
[07:28] 100 lines of code of like very simple python
[07:30] python which we'll understand by the end of
[07:31] which we'll understand by the end of this lecture
[07:32] this lecture and then nn.pi
[07:33] and then nn.pi this neural network library built on top
[07:35] this neural network library built on top of the autograd engine
[07:37] of the autograd engine um is like a joke it's like
[07:40] um is like a joke it's like we have to define what is a neuron and
[07:42] we have to define what is a neuron and then we have to define what is the layer
[07:44] then we have to define what is the layer of neurons and then we define what is a
[07:46] of neurons and then we define what is a multi-layer perceptron which is just a
[07:47] multi-layer perceptron which is just a sequence of layers of neurons and so
[07:50] sequence of layers of neurons and so it's just a total joke
[07:52] it's just a total joke so basically
[07:53] so basically there's a lot of power that comes from
[07:55] there's a lot of power that comes from only 150 lines of code
[07:57] only 150 lines of code and that's all you need to understand to
[07:59] and that's all you need to understand to understand neural network training and
[08:00] understand neural network training and everything else is just efficiency and
[08:02] everything else is just efficiency and of course there's a lot to efficiency
[08:05] of course there's a lot to efficiency but fundamentally that's all that's
[08:07] but fundamentally that's all that's happening okay so now let's dive right
[08:09] happening okay so now let's dive right in and implement micrograph step by step
[08:11] in and implement micrograph step by step the first thing i'd like to do is i'd
[08:12] the first thing i'd like to do is i'd like to make sure that you have a very
[08:13] like to make sure that you have a very good understanding intuitively of what a
[08:16] good understanding intuitively of what a derivative is and exactly what
[08:18] derivative is and exactly what information it gives you so let's start
[08:20] information it gives you so let's start with some basic imports that i copy
[08:22] with some basic imports that i copy paste in every jupiter notebook always
[08:25] paste in every jupiter notebook always and let's define a function a scalar
[08:27] and let's define a function a scalar valued function
[08:28] valued function f of x
[08:30] f of x as follows
[08:31] as follows so i just make this up randomly i just
[08:33] so i just make this up randomly i just want to scale a valid function that
[08:34] want to scale a valid function that takes a single scalar x and returns a
[08:36] takes a single scalar x and returns a single scalar y
[08:38] single scalar y and we can call this function of course
[08:40] and we can call this function of course so we can pass in say 3.0 and get 20
[08:42] so we can pass in say 3.0 and get 20 back
[08:43] back now we can also plot this function to
[08:45] now we can also plot this function to get a sense of its shape you can tell
[08:47] get a sense of its shape you can tell from the mathematical expression that
[08:48] from the mathematical expression that this is probably a parabola it's a
[08:50] this is probably a parabola it's a quadratic
[08:51] quadratic and so if we just uh create a set of um
[08:56] and so if we just uh create a set of um um
[08:57] um scale values that we can feed in using
[08:59] scale values that we can feed in using for example a range from negative five
[09:01] for example a range from negative five to five in steps of 0.25
[09:03] to five in steps of 0.25 so this is so axis is just from negative
[09:06] so this is so axis is just from negative 5 to 5 not including 5 in steps of 0.25
[09:11] 5 to 5 not including 5 in steps of 0.25 and we can actually call this function
[09:12] and we can actually call this function on this numpy array as well so we get a
[09:14] on this numpy array as well so we get a set of y's if we call f on axis
[09:17] set of y's if we call f on axis and these y's are basically
[09:20] and these y's are basically also applying a function on every one of
[09:23] also applying a function on every one of these elements independently
[09:25] these elements independently and we can plot this using matplotlib so
[09:28] and we can plot this using matplotlib so plt.plot x's and y's and we get a nice
[09:31] plt.plot x's and y's and we get a nice parabola so previously here we fed in
[09:33] parabola so previously here we fed in 3.0 somewhere here and we received 20
[09:36] 3.0 somewhere here and we received 20 back which is here the y coordinate so
[09:39] back which is here the y coordinate so now i'd like to think through
[09:40] now i'd like to think through what is the derivative
[09:42] what is the derivative of this function at any single input
[09:44] of this function at any single input point x
[09:45] point x right so what is the derivative at
[09:47] right so what is the derivative at different points x of this function now
[09:49] different points x of this function now if you remember back to your calculus
[09:51] if you remember back to your calculus class you've probably derived
[09:52] class you've probably derived derivatives so we take this mathematical
[09:54] derivatives so we take this mathematical expression 3x squared minus 4x plus 5
[09:57] expression 3x squared minus 4x plus 5 and you would write out on a piece of
[09:58] and you would write out on a piece of paper and you would you know apply the
[09:59] paper and you would you know apply the product rule and all the other rules and
[10:01] product rule and all the other rules and derive the mathematical expression of
[10:03] derive the mathematical expression of the great derivative of the original
[10:05] the great derivative of the original function and then you could plug in
[10:06] function and then you could plug in different texts and see what the
[10:08] different texts and see what the derivative is
[10:09] derivative is we're not going to actually do that
[10:11] we're not going to actually do that because no one in neural networks
[10:13] because no one in neural networks actually writes out the expression for
[10:15] actually writes out the expression for the neural net it would be a massive
[10:16] the neural net it would be a massive expression um it would be you know
[10:18] expression um it would be you know thousands tens of thousands of terms no
[10:20] thousands tens of thousands of terms no one actually derives the derivative of
[10:22] one actually derives the derivative of course and so we're not going to take
[10:24] course and so we're not going to take this kind of like a symbolic approach
[10:26] this kind of like a symbolic approach instead what i'd like to do is i'd like
[10:27] instead what i'd like to do is i'd like to look at the definition of derivative
[10:29] to look at the definition of derivative and just make sure that we really
[10:30] and just make sure that we really understand what derivative is measuring
[10:32] understand what derivative is measuring what it's telling you about the function
[10:34] what it's telling you about the function and so if we just look up derivative
[10:42] we see that okay so this is not a very good
[10:44] okay so this is not a very good definition of derivative this is a
[10:46] definition of derivative this is a definition of what it means to be
[10:47] definition of what it means to be differentiable
[10:48] differentiable but if you remember from your calculus
[10:50] but if you remember from your calculus it is the limit as h goes to zero of f
[10:52] it is the limit as h goes to zero of f of x plus h minus f of x over h so
[10:55] of x plus h minus f of x over h so basically what it's saying is if you
[10:58] basically what it's saying is if you slightly bump up you're at some point x
[11:00] slightly bump up you're at some point x that you're interested in or a and if
[11:02] that you're interested in or a and if you slightly bump up
[11:04] you slightly bump up you know you slightly increase it by
[11:06] you know you slightly increase it by small number h
[11:08] small number h how does the function respond with what
[11:09] how does the function respond with what sensitivity does it respond what is the
[11:11] sensitivity does it respond what is the slope at that point does the function go
[11:13] slope at that point does the function go up or does it go down and by how much
[11:16] up or does it go down and by how much and that's the slope of that function
[11:18] and that's the slope of that function the
[11:18] the the slope of that response at that point
[11:21] the slope of that response at that point and so we can basically evaluate
[11:23] and so we can basically evaluate the derivative here numerically by
[11:26] the derivative here numerically by taking a very small h of course the
[11:28] taking a very small h of course the definition would ask us to take h to
[11:30] definition would ask us to take h to zero we're just going to pick a very
[11:31] zero we're just going to pick a very small h 0.001
[11:34] small h 0.001 and let's say we're interested in point
[11:35] and let's say we're interested in point 3.0 so we can look at f of x of course
[11:37] 3.0 so we can look at f of x of course as 20
[11:38] as 20 and now f of x plus h
[11:40] and now f of x plus h so if we slightly nudge x in a positive
[11:42] so if we slightly nudge x in a positive direction how is the function going to
[11:44] direction how is the function going to respond
[11:45] respond and just looking at this do you expect
[11:47] and just looking at this do you expect do you expect f of x plus h to be
[11:49] do you expect f of x plus h to be slightly greater than 20 or do you
[11:51] slightly greater than 20 or do you expect to be slightly lower than 20
[11:54] expect to be slightly lower than 20 and since this 3 is here and this is 20
[11:57] and since this 3 is here and this is 20 if we slightly go positively the
[11:59] if we slightly go positively the function will respond positively so
[12:01] function will respond positively so you'd expect this to be slightly greater
[12:03] you'd expect this to be slightly greater than 20. and now by how much it's
[12:05] than 20. and now by how much it's telling you the
[12:06] telling you the sort of the
[12:07] sort of the the strength of that slope right the the
[12:09] the strength of that slope right the the size of the slope so f of x plus h minus
[12:12] size of the slope so f of x plus h minus f of x this is how much the function
[12:14] f of x this is how much the function responded
[12:16] responded in the positive direction and we have to
[12:17] in the positive direction and we have to normalize by the
[12:19] normalize by the run so we have the rise over run to get
[12:22] run so we have the rise over run to get the slope so this of course is just a
[12:24] the slope so this of course is just a numerical approximation of the slope
[12:26] numerical approximation of the slope because we have to make age very very
[12:28] because we have to make age very very small to converge to the exact amount
[12:32] small to converge to the exact amount now if i'm doing too many zeros
[12:35] now if i'm doing too many zeros at some point
[12:36] at some point i'm gonna get an incorrect answer
[12:38] i'm gonna get an incorrect answer because we're using floating point
[12:39] because we're using floating point arithmetic and the representations of
[12:41] arithmetic and the representations of all these numbers in computer memory is
[12:43] all these numbers in computer memory is finite and at some point we get into
[12:45] finite and at some point we get into trouble
[12:46] trouble so we can converse towards the right
[12:47] so we can converse towards the right answer with this approach
[12:50] answer with this approach but basically um at 3 the slope is 14.
[12:54] but basically um at 3 the slope is 14. and you can see that by taking 3x
[12:56] and you can see that by taking 3x squared minus 4x plus 5 and
[12:58] squared minus 4x plus 5 and differentiating it in our head
[13:00] differentiating it in our head so 3x squared would be
[13:02] so 3x squared would be 6 x minus 4
[13:04] 6 x minus 4 and then we plug in x equals 3 so that's
[13:07] and then we plug in x equals 3 so that's 18 minus 4 is 14. so this is correct
[13:10] 18 minus 4 is 14. so this is correct so that's
[13:12] so that's at 3. now how about the slope at say
[13:15] at 3. now how about the slope at say negative 3
[13:17] negative 3 would you expect would you expect for
[13:19] would you expect would you expect for the slope
[13:20] the slope now telling the exact value is really
[13:22] now telling the exact value is really hard but what is the sign of that slope
[13:24] hard but what is the sign of that slope so at negative three
[13:26] so at negative three if we slightly go in the positive
[13:28] if we slightly go in the positive direction at x the function would
[13:30] direction at x the function would actually go down and so that tells you
[13:32] actually go down and so that tells you that the slope would be negative so
[13:33] that the slope would be negative so we'll get a slight number below
[13:36] we'll get a slight number below below 20. and so if we take the slope we
[13:39] below 20. and so if we take the slope we expect something negative
[13:40] expect something negative negative 22. okay
[13:43] negative 22. okay and at some point here of course the
[13:45] and at some point here of course the slope would be zero now for this
[13:47] slope would be zero now for this specific function i looked it up
[13:48] specific function i looked it up previously and it's at point two over
[13:51] previously and it's at point two over three
[13:52] three so at roughly two over three
[13:54] so at roughly two over three uh that's somewhere here
[13:55] uh that's somewhere here um
[13:57] um this derivative be zero
[13:59] this derivative be zero so basically at that precise point
[14:03] so basically at that precise point yeah
[14:04] yeah at that precise point if we nudge in a
[14:06] at that precise point if we nudge in a positive direction the function doesn't
[14:07] positive direction the function doesn't respond this stays the same almost and
[14:09] respond this stays the same almost and so that's why the slope is zero okay now
[14:11] so that's why the slope is zero okay now let's look at a bit more complex case
[14:14] let's look at a bit more complex case so we're going to start you know
[14:15] so we're going to start you know complexifying a bit so now we have a
[14:18] complexifying a bit so now we have a function
[14:19] function here
[14:20] here with output variable d
[14:22] with output variable d that is a function of three scalar
[14:24] that is a function of three scalar inputs a b and c
[14:26] inputs a b and c so a b and c are some specific values
[14:28] so a b and c are some specific values three inputs into our expression graph
[14:30] three inputs into our expression graph and a single output d
[14:32] and a single output d and so if we just print d we get four
[14:36] and so if we just print d we get four and now what i have to do is i'd like to
[14:38] and now what i have to do is i'd like to again look at the derivatives of d with
[14:40] again look at the derivatives of d with respect to a b and c
[14:42] respect to a b and c and uh think through uh again just the
[14:44] and uh think through uh again just the intuition of what this derivative is
[14:46] intuition of what this derivative is telling us
[14:47] telling us so in order to evaluate this derivative
[14:49] so in order to evaluate this derivative we're going to get a bit hacky here
[14:52] we're going to get a bit hacky here we're going to again have a very small
[14:53] we're going to again have a very small value of h
[14:55] value of h and then we're going to fix the inputs
[14:57] and then we're going to fix the inputs at some
[14:58] at some values that we're interested in
[15:00] values that we're interested in so these are the this is the point abc
[15:02] so these are the this is the point abc at which we're going to be evaluating
[15:04] at which we're going to be evaluating the the
[15:05] the the derivative of d with respect to all a b
[15:07] derivative of d with respect to all a b and c at that point
[15:09] and c at that point so there are the inputs and now we have
[15:11] so there are the inputs and now we have d1 is that expression
[15:13] d1 is that expression and then we're going to for example look
[15:15] and then we're going to for example look at the derivative of d with respect to a
[15:17] at the derivative of d with respect to a so we'll take a and we'll bump it by h
[15:19] so we'll take a and we'll bump it by h and then we'll get d2 to be the exact
[15:22] and then we'll get d2 to be the exact same function
[15:23] same function and now we're going to print um
[15:26] and now we're going to print um you know f1
[15:28] you know f1 d1 is d1
[15:31] d1 is d1 d2 is d2
[15:32] d2 is d2 and print slope
[15:35] and print slope so the derivative or slope
[15:37] so the derivative or slope here will be um
[15:39] here will be um of course
[15:41] of course d2
[15:42] d2 minus d1 divide h
[15:44] minus d1 divide h so d2 minus d1 is how much the function
[15:47] so d2 minus d1 is how much the function increased
[15:48] increased uh when we bumped
[15:50] uh when we bumped the uh
[15:51] the uh the specific input that we're interested
[15:53] the specific input that we're interested in by a tiny amount
[15:55] in by a tiny amount and
[15:56] and this is then normalized by h
[15:59] this is then normalized by h to get the slope
[16:02] so um
[16:05] um yeah
[16:06] yeah so this so if i just run this we're
[16:08] so this so if i just run this we're going to print
[16:10] going to print d1
[16:12] d1 which we know is four
[16:15] which we know is four now d2 will be bumped a will be bumped
[16:18] now d2 will be bumped a will be bumped by h
[16:20] by h so let's just think through
[16:22] so let's just think through a little bit uh what d2 will be uh
[16:26] a little bit uh what d2 will be uh printed out here
[16:27] printed out here in particular
[16:29] in particular d1 will be four
[16:31] d1 will be four will d2 be a number slightly greater
[16:33] will d2 be a number slightly greater than four or slightly lower than four
[16:35] than four or slightly lower than four and that's going to tell us the sl the
[16:37] and that's going to tell us the sl the the sign of the derivative
[16:40] the sign of the derivative so
[16:42] we're bumping a by h
[16:45] we're bumping a by h b as minus three c is ten
[16:48] b as minus three c is ten so you can just intuitively think
[16:49] so you can just intuitively think through this derivative and what it's
[16:51] through this derivative and what it's doing a will be slightly more positive
[16:54] doing a will be slightly more positive and but b is a negative number
[16:57] and but b is a negative number so if a is slightly more positive
[17:00] so if a is slightly more positive because b is negative three
[17:03] because b is negative three we're actually going to be adding less
[17:06] we're actually going to be adding less to d
[17:08] to d so you'd actually expect that the value
[17:10] so you'd actually expect that the value of the function will go down
[17:13] of the function will go down so let's just see this
[17:16] so let's just see this yeah and so we went from 4
[17:18] yeah and so we went from 4 to 3.9996
[17:20] to 3.9996 and that tells you that the slope will
[17:22] and that tells you that the slope will be negative
[17:23] be negative and then
[17:24] and then uh will be a negative number
[17:26] uh will be a negative number because we went down
[17:27] because we went down and then
[17:29] and then the exact number of slope will be
[17:31] the exact number of slope will be exact amount of slope is negative 3.
[17:33] exact amount of slope is negative 3. and you can also convince yourself that
[17:35] and you can also convince yourself that negative 3 is the right answer
[17:36] negative 3 is the right answer mathematically and analytically because
[17:39] mathematically and analytically because if you have a times b plus c and you are
[17:41] if you have a times b plus c and you are you know you have calculus then
[17:43] you know you have calculus then differentiating a times b plus c with
[17:46] differentiating a times b plus c with respect to a gives you just b
[17:48] respect to a gives you just b and indeed the value of b is negative 3
[17:50] and indeed the value of b is negative 3 which is the derivative that we have so
[17:52] which is the derivative that we have so you can tell that that's correct
[17:54] you can tell that that's correct so now if we do this with b
[17:57] so now if we do this with b so if we bump b by a little bit in a
[17:59] so if we bump b by a little bit in a positive direction we'd get different
[18:02] positive direction we'd get different slopes so what is the influence of b on
[18:04] slopes so what is the influence of b on the output d
[18:06] the output d so if we bump b by a tiny amount in a
[18:08] so if we bump b by a tiny amount in a positive direction then because a is
[18:10] positive direction then because a is positive
[18:11] positive we'll be adding more to d
[18:13] we'll be adding more to d right
[18:14] right so um and now what is the what is the
[18:17] so um and now what is the what is the sensitivity what is the slope of that
[18:18] sensitivity what is the slope of that addition
[18:19] addition and it might not surprise you that this
[18:21] and it might not surprise you that this should be
[18:22] should be 2
[18:24] 2 and y is a 2 because d of d
[18:27] and y is a 2 because d of d by db differentiating with respect to b
[18:30] by db differentiating with respect to b would be would give us a
[18:31] would be would give us a and the value of a is two so that's also
[18:34] and the value of a is two so that's also working well
[18:35] working well and then if c gets bumped a tiny amount
[18:37] and then if c gets bumped a tiny amount in h
[18:38] in h by h
[18:39] by h then of course a times b is unaffected
[18:41] then of course a times b is unaffected and now c becomes slightly bit higher
[18:44] and now c becomes slightly bit higher what does that do to the function it
[18:45] what does that do to the function it makes it slightly bit higher because
[18:47] makes it slightly bit higher because we're simply adding c
[18:48] we're simply adding c and it makes it slightly bit higher by
[18:50] and it makes it slightly bit higher by the exact same amount that we added to c
[18:53] the exact same amount that we added to c and so that tells you that the slope is
[18:55] and so that tells you that the slope is one
[18:56] one that will be the
[18:59] that will be the the rate at which
[19:01] the rate at which d will increase as we scale
[19:04] d will increase as we scale c
[19:05] c okay so we now have some intuitive sense
[19:06] okay so we now have some intuitive sense of what this derivative is telling you
[19:08] of what this derivative is telling you about the function and we'd like to move
[19:10] about the function and we'd like to move to neural networks now as i mentioned
[19:11] to neural networks now as i mentioned neural networks will be pretty massive
[19:13] neural networks will be pretty massive expressions mathematical expressions so
[19:15] expressions mathematical expressions so we need some data structures that
[19:16] we need some data structures that maintain these expressions and that's
[19:17] maintain these expressions and that's what we're going to start to build out
[19:19] what we're going to start to build out now
[19:20] now so we're going to
[19:22] so we're going to build out this value object that i
[19:24] build out this value object that i showed you in the readme page of
[19:26] showed you in the readme page of micrograd
[19:27] micrograd so let me copy paste a skeleton of the
[19:30] so let me copy paste a skeleton of the first very simple value object
[19:33] first very simple value object so class value takes a single
[19:36] so class value takes a single scalar value that it wraps and keeps
[19:38] scalar value that it wraps and keeps track of
[19:39] track of and that's it so
[19:41] and that's it so we can for example do value of 2.0 and
[19:43] we can for example do value of 2.0 and then we can
[19:45] then we can get we can look at its content and
[19:48] get we can look at its content and python will internally
[19:50] python will internally use the wrapper function
[19:52] use the wrapper function to uh return
[19:54] to uh return uh this string oops
[19:56] uh this string oops like that
[19:58] like that so this is a value object with data
[20:00] so this is a value object with data equals two that we're creating here
[20:03] equals two that we're creating here now we'd like to do is like we'd like to
[20:04] now we'd like to do is like we'd like to be able to
[20:07] be able to have not just like two values
[20:10] have not just like two values but we'd like to do a bluffy right we'd
[20:12] but we'd like to do a bluffy right we'd like to add them
[20:13] like to add them so currently you would get an error
[20:15] so currently you would get an error because python doesn't know how to add
[20:17] because python doesn't know how to add two value objects so we have to tell it
[20:21] two value objects so we have to tell it so here's
[20:22] so here's addition
[20:26] so you have to basically use these special double underscore methods in
[20:29] special double underscore methods in python to define these operators for
[20:31] python to define these operators for these objects so if we call um
[20:35] these objects so if we call um the uh if we use this plus operator
[20:39] the uh if we use this plus operator python will internally call a dot add of
[20:43] python will internally call a dot add of b
[20:43] b that's what will happen internally and
[20:45] that's what will happen internally and so b will be the other and
[20:48] so b will be the other and self will be a
[20:50] self will be a and so we see that what we're going to
[20:52] and so we see that what we're going to return is a new value object and it's
[20:54] return is a new value object and it's just it's going to be wrapping
[20:56] just it's going to be wrapping the plus of
[20:58] the plus of their data
[20:59] their data but remember now because data is the
[21:02] but remember now because data is the actual like numbered python number so
[21:04] actual like numbered python number so this operator here is just the typical
[21:06] this operator here is just the typical floating point plus addition now it's
[21:09] floating point plus addition now it's not an addition of value objects
[21:11] not an addition of value objects and will return a new value so now a
[21:14] and will return a new value so now a plus b should work and it should print
[21:16] plus b should work and it should print value of
[21:17] value of negative one
[21:18] negative one because that's two plus minus three
[21:20] because that's two plus minus three there we go
[21:21] there we go okay let's now implement multiply
[21:24] okay let's now implement multiply just so we can recreate this expression
[21:25] just so we can recreate this expression here
[21:26] here so multiply i think it won't surprise
[21:28] so multiply i think it won't surprise you will be fairly similar
[21:31] you will be fairly similar so instead of add we're going to be
[21:33] so instead of add we're going to be using mul
[21:34] using mul and then here of course we want to do
[21:36] and then here of course we want to do times
[21:36] times and so now we can create a c value
[21:38] and so now we can create a c value object which will be 10.0 and now we
[21:41] object which will be 10.0 and now we should be able to do a times b well
[21:44] should be able to do a times b well let's just do a times b first
[21:46] let's just do a times b first um
[21:47] um [Music]
[21:48] [Music] that's value of negative six now
[21:50] that's value of negative six now and by the way i skipped over this a
[21:52] and by the way i skipped over this a little bit suppose that i didn't have
[21:53] little bit suppose that i didn't have the wrapper function here
[21:55] the wrapper function here then it's just that you'll get some kind
[21:57] then it's just that you'll get some kind of an ugly expression so what wrapper is
[21:59] of an ugly expression so what wrapper is doing is it's providing us a way to
[22:02] doing is it's providing us a way to print out like a nicer looking
[22:03] print out like a nicer looking expression in python
[22:05] expression in python uh so we don't just have something
[22:07] uh so we don't just have something cryptic we actually are you know it's
[22:09] cryptic we actually are you know it's value of
[22:10] value of negative six so this gives us a times
[22:13] negative six so this gives us a times and then this we should now be able to
[22:16] and then this we should now be able to add c to it because we've defined and
[22:18] add c to it because we've defined and told the python how to do mul and add
[22:20] told the python how to do mul and add and so this will call this will
[22:22] and so this will call this will basically be equivalent to a dot
[22:24] basically be equivalent to a dot small
[22:26] small of b
[22:27] of b and then this new value object will be
[22:29] and then this new value object will be dot add
[22:31] dot add of c
[22:32] of c and so let's see if that worked
[22:34] and so let's see if that worked yep so that worked well that gave us
[22:36] yep so that worked well that gave us four which is what we expect from before
[22:39] four which is what we expect from before and i believe we can just call them
[22:40] and i believe we can just call them manually as well there we go so
[22:44] manually as well there we go so yeah
[22:45] yeah okay so now what we are missing is the
[22:46] okay so now what we are missing is the connective tissue of this expression as
[22:49] connective tissue of this expression as i mentioned we want to keep these
[22:50] i mentioned we want to keep these expression graphs so we need to know and
[22:52] expression graphs so we need to know and keep pointers about what values produce
[22:54] keep pointers about what values produce what other values
[22:56] what other values so here for example we are going to
[22:58] so here for example we are going to introduce a new variable which we'll
[23:00] introduce a new variable which we'll call children and by default it will be
[23:02] call children and by default it will be an empty tuple
[23:03] an empty tuple and then we're actually going to keep a
[23:04] and then we're actually going to keep a slightly different variable in the class
[23:06] slightly different variable in the class which we'll call underscore prev which
[23:08] which we'll call underscore prev which will be the set of children
[23:11] will be the set of children this is how i done i did it in the
[23:13] this is how i done i did it in the original micrograd looking at my code
[23:15] original micrograd looking at my code here i can't remember exactly the reason
[23:17] here i can't remember exactly the reason i believe it was efficiency but this
[23:19] i believe it was efficiency but this underscore children will be a tuple for
[23:20] underscore children will be a tuple for convenience but then when we actually
[23:22] convenience but then when we actually maintain it in the class it will be just
[23:23] maintain it in the class it will be just this set yeah i believe for efficiency
[23:27] this set yeah i believe for efficiency um
[23:28] um so now
[23:29] so now when we are creating a value like this
[23:31] when we are creating a value like this with a constructor children will be
[23:33] with a constructor children will be empty and prep will be the empty set but
[23:36] empty and prep will be the empty set but when we're creating a value through
[23:37] when we're creating a value through addition or multiplication we're going
[23:39] addition or multiplication we're going to feed in the children of this value
[23:42] to feed in the children of this value which in this case is self and other
[23:46] which in this case is self and other so those are the children
[23:48] so those are the children here
[23:50] here so now we can do d dot prev
[23:52] so now we can do d dot prev and we'll see that the children of the
[23:55] and we'll see that the children of the we now know are this value of negative 6
[23:58] we now know are this value of negative 6 and value of 10 and this of course is
[24:00] and value of 10 and this of course is the value resulting from a times b and
[24:03] the value resulting from a times b and the c value which is 10.
[24:06] the c value which is 10. now the last piece of information we
[24:08] now the last piece of information we don't know so we know that the children
[24:10] don't know so we know that the children of every single value but we don't know
[24:12] of every single value but we don't know what operation created this value
[24:14] what operation created this value so we need one more element here let's
[24:16] so we need one more element here let's call it underscore pop
[24:19] call it underscore pop and by default this is the empty set for
[24:21] and by default this is the empty set for leaves
[24:22] leaves and then we'll just maintain it here
[24:25] and then we'll just maintain it here and now the operation will be just a
[24:27] and now the operation will be just a simple string and in the case of
[24:29] simple string and in the case of addition it's plus in the case of
[24:31] addition it's plus in the case of multiplication is times
[24:33] multiplication is times so now we
[24:35] so now we not just have d dot pref we also have a
[24:37] not just have d dot pref we also have a d dot up
[24:38] d dot up and we know that d was produced by an
[24:40] and we know that d was produced by an addition of those two values and so now
[24:42] addition of those two values and so now we have the full
[24:44] we have the full mathematical expression uh and we're
[24:46] mathematical expression uh and we're building out this data structure and we
[24:47] building out this data structure and we know exactly how each value came to be
[24:49] know exactly how each value came to be by word expression and from what other
[24:51] by word expression and from what other values
[24:54] now because these expressions are about to get quite a bit larger we'd like a
[24:58] to get quite a bit larger we'd like a way to nicely visualize these
[25:00] way to nicely visualize these expressions that we're building out so
[25:02] expressions that we're building out so for that i'm going to copy paste a bunch
[25:03] for that i'm going to copy paste a bunch of slightly scary code that's going to
[25:06] of slightly scary code that's going to visualize this these expression graphs
[25:08] visualize this these expression graphs for us
[25:09] for us so here's the code and i'll explain it
[25:11] so here's the code and i'll explain it in a bit but first let me just show you
[25:13] in a bit but first let me just show you what this code does
[25:14] what this code does basically what it does is it creates a
[25:16] basically what it does is it creates a new function drawdot that we can call on
[25:19] new function drawdot that we can call on some root node
[25:20] some root node and then it's going to visualize it so
[25:22] and then it's going to visualize it so if we call drawdot on d
[25:24] if we call drawdot on d which is this final value here that is a
[25:27] which is this final value here that is a times b plus c
[25:29] times b plus c it creates something like this so this
[25:31] it creates something like this so this is d
[25:32] is d and you see that this is a times b
[25:34] and you see that this is a times b creating an integrated value plus c
[25:36] creating an integrated value plus c gives us this output node d
[25:40] gives us this output node d so that's dried out of d
[25:42] so that's dried out of d and i'm not going to go through this in
[25:44] and i'm not going to go through this in complete detail you can take a look at
[25:46] complete detail you can take a look at graphless and its api uh graphis is a
[25:48] graphless and its api uh graphis is a open source graph visualization software
[25:51] open source graph visualization software and what we're doing here is we're
[25:52] and what we're doing here is we're building out this graph and graphis
[25:54] building out this graph and graphis api and
[25:56] api and you can basically see that trace is this
[25:58] you can basically see that trace is this helper function that enumerates all of
[26:00] helper function that enumerates all of the nodes and edges in the graph
[26:02] the nodes and edges in the graph so that just builds a set of all the
[26:04] so that just builds a set of all the nodes and edges and then we iterate for
[26:06] nodes and edges and then we iterate for all the nodes and we create special node
[26:08] all the nodes and we create special node objects
[26:08] objects for them in
[26:11] for them in using dot node
[26:13] using dot node and then we also create edges using dot
[26:15] and then we also create edges using dot dot edge
[26:16] dot edge and the only thing that's like slightly
[26:18] and the only thing that's like slightly tricky here is you'll notice that i
[26:20] tricky here is you'll notice that i basically add these fake nodes which are
[26:22] basically add these fake nodes which are these operation nodes so for example
[26:24] these operation nodes so for example this node here is just like a plus node
[26:27] this node here is just like a plus node and
[26:28] and i create these
[26:31] i create these special op nodes here
[26:34] special op nodes here and i connect them accordingly so these
[26:37] and i connect them accordingly so these nodes of course are not actual
[26:39] nodes of course are not actual nodes in the original graph
[26:41] nodes in the original graph they're not actually a value object the
[26:43] they're not actually a value object the only value objects here are the things
[26:46] only value objects here are the things in squares those are actual value
[26:48] in squares those are actual value objects or representations thereof and
[26:50] objects or representations thereof and these op nodes are just created in this
[26:52] these op nodes are just created in this drawdot routine so that it looks nice
[26:55] drawdot routine so that it looks nice let's also add labels to these graphs
[26:57] let's also add labels to these graphs just so we know what variables are where
[26:59] just so we know what variables are where so let's create a special underscore
[27:01] so let's create a special underscore label
[27:02] label um
[27:03] um or let's just do label
[27:05] or let's just do label equals empty by default and save it in
[27:08] equals empty by default and save it in each node
[27:11] and then here we're going to do label as a
[27:15] a label is the
[27:17] label is the label a c
[27:22] and then let's create a special um
[27:27] let's create a special um e equals a times b
[27:30] and e dot label will be e
[27:34] and e dot label will be e it's kind of naughty
[27:35] it's kind of naughty and e will be e plus c
[27:38] and e will be e plus c and a d dot label will be
[27:40] and a d dot label will be d
[27:42] d okay so nothing really changes i just
[27:44] okay so nothing really changes i just added this new e function
[27:46] added this new e function a new e variable
[27:48] a new e variable and then here when we are
[27:50] and then here when we are printing this
[27:51] printing this i'm going to print the label here so
[27:54] i'm going to print the label here so this will be a percent s
[27:56] this will be a percent s bar
[27:56] bar and this will be end.label
[28:01] and so now we have the label on the left here so it
[28:05] we have the label on the left here so it says a b creating e and then e plus c
[28:07] says a b creating e and then e plus c creates d
[28:08] creates d just like we have it here
[28:10] just like we have it here and finally let's make this expression
[28:12] and finally let's make this expression just one layer deeper
[28:14] just one layer deeper so d will not be the final output node
[28:17] so d will not be the final output node instead after d we are going to create a
[28:20] instead after d we are going to create a new value object
[28:21] new value object called f we're going to start running
[28:23] called f we're going to start running out of variables soon f will be negative
[28:25] out of variables soon f will be negative 2.0
[28:27] 2.0 and its label will of course just be f
[28:30] and its label will of course just be f and then l capital l will be the output
[28:34] and then l capital l will be the output of our graph
[28:35] of our graph and l will be p times f
[28:38] and l will be p times f okay
[28:38] okay so l will be negative eight is the
[28:40] so l will be negative eight is the output
[28:44] so now we don't just draw a d we draw l
[28:50] okay and somehow the label of
[28:53] and somehow the label of l was undefined oops all that label has
[28:56] l was undefined oops all that label has to be explicitly sort of given to it
[28:59] to be explicitly sort of given to it there we go so l is the output
[29:01] there we go so l is the output so let's quickly recap what we've done
[29:03] so let's quickly recap what we've done so far
[29:04] so far we are able to build out mathematical
[29:05] we are able to build out mathematical expressions using only plus and times so
[29:08] expressions using only plus and times so far
[29:09] far they are scalar valued along the way
[29:11] they are scalar valued along the way and we can do this forward pass
[29:14] and we can do this forward pass and build out a mathematical expression
[29:16] and build out a mathematical expression so we have multiple inputs here a b c
[29:18] so we have multiple inputs here a b c and f
[29:19] and f going into a mathematical expression
[29:21] going into a mathematical expression that produces a single output l
[29:24] that produces a single output l and this here is visualizing the forward
[29:26] and this here is visualizing the forward pass so the output of the forward pass
[29:28] pass so the output of the forward pass is negative eight that's the value
[29:31] is negative eight that's the value now what we'd like to do next is we'd
[29:33] now what we'd like to do next is we'd like to run back propagation
[29:35] like to run back propagation and in back propagation we are going to
[29:37] and in back propagation we are going to start here at the end and we're going to
[29:39] start here at the end and we're going to reverse
[29:40] reverse and calculate the gradient along along
[29:43] and calculate the gradient along along all these intermediate values
[29:45] all these intermediate values and really what we're computing for
[29:46] and really what we're computing for every single value here
[29:48] every single value here um we're going to compute the derivative
[29:50] um we're going to compute the derivative of that node with respect to l
[29:55] of that node with respect to l so
[29:56] so the derivative of l with respect to l is
[29:58] the derivative of l with respect to l is just uh one
[30:00] just uh one and then we're going to derive what is
[30:01] and then we're going to derive what is the derivative of l with respect to f
[30:03] the derivative of l with respect to f with respect to d with respect to c with
[30:06] with respect to d with respect to c with respect to e
[30:07] respect to e with respect to b and with respect to a
[30:10] with respect to b and with respect to a and in the neural network setting you'd
[30:12] and in the neural network setting you'd be very interested in the derivative of
[30:13] be very interested in the derivative of basically this loss function l
[30:16] basically this loss function l with respect to the weights of a neural
[30:18] with respect to the weights of a neural network
[30:19] network and here of course we have just these
[30:20] and here of course we have just these variables a b c and f
[30:22] variables a b c and f but some of these will eventually
[30:23] but some of these will eventually represent the weights of a neural net
[30:25] represent the weights of a neural net and so we'll need to know how those
[30:27] and so we'll need to know how those weights are impacting
[30:29] weights are impacting the loss function so we'll be interested
[30:31] the loss function so we'll be interested basically in the derivative of the
[30:32] basically in the derivative of the output with respect to some of its leaf
[30:34] output with respect to some of its leaf nodes and those leaf nodes will be the
[30:36] nodes and those leaf nodes will be the weights of the neural net
[30:38] weights of the neural net and the other leaf nodes of course will
[30:39] and the other leaf nodes of course will be the data itself but usually we will
[30:41] be the data itself but usually we will not want or use the derivative of the
[30:44] not want or use the derivative of the loss function with respect to data
[30:45] loss function with respect to data because the data is fixed but the
[30:47] because the data is fixed but the weights will be iterated on
[30:50] weights will be iterated on using the gradient information so next
[30:52] using the gradient information so next we are going to create a variable inside
[30:54] we are going to create a variable inside the value class that maintains the
[30:57] the value class that maintains the derivative of l with respect to that
[30:59] derivative of l with respect to that value
[31:00] value and we will call this variable grad
[31:03] and we will call this variable grad so there's a data and there's a
[31:05] so there's a data and there's a self.grad
[31:07] self.grad and initially it will be zero and
[31:09] and initially it will be zero and remember that zero is basically means no
[31:12] remember that zero is basically means no effect so at initialization we're
[31:14] effect so at initialization we're assuming that every value does not
[31:16] assuming that every value does not impact does not affect the out the
[31:18] impact does not affect the out the output
[31:19] output right because if the gradient is zero
[31:21] right because if the gradient is zero that means that changing this variable
[31:23] that means that changing this variable is not changing the loss function
[31:25] is not changing the loss function so by default we assume that the
[31:27] so by default we assume that the gradient is zero
[31:28] gradient is zero and then
[31:31] and then now that we have grad and it's 0.0
[31:36] we are going to be able to visualize it here after data so here grad is 0.4 f
[31:42] here after data so here grad is 0.4 f and this will be in that graph
[31:45] and this will be in that graph and now we are going to be showing both
[31:47] and now we are going to be showing both the data and the grad
[31:50] the data and the grad initialized at zero
[31:53] initialized at zero and we are just about getting ready to
[31:55] and we are just about getting ready to calculate the back propagation
[31:57] calculate the back propagation and of course this grad again as i
[31:58] and of course this grad again as i mentioned is representing
[32:00] mentioned is representing the derivative of the output in this
[32:02] the derivative of the output in this case l with respect to this value so
[32:05] case l with respect to this value so with respect to so this is the
[32:06] with respect to so this is the derivative of l with respect to f with
[32:08] derivative of l with respect to f with respect to d and so on so let's now fill
[32:11] respect to d and so on so let's now fill in those gradients and actually do back
[32:12] in those gradients and actually do back propagation manually so let's start
[32:14] propagation manually so let's start filling in these gradients and start all
[32:16] filling in these gradients and start all the way at the end as i mentioned here
[32:18] the way at the end as i mentioned here first we are interested to fill in this
[32:20] first we are interested to fill in this gradient here so what is the derivative
[32:22] gradient here so what is the derivative of l with respect to l
[32:25] of l with respect to l in other words if i change l by a tiny
[32:27] in other words if i change l by a tiny amount of h
[32:29] amount of h how much does
[32:30] how much does l change
[32:32] l change it changes by h so it's proportional and
[32:35] it changes by h so it's proportional and therefore derivative will be one
[32:37] therefore derivative will be one we can of course measure these or
[32:39] we can of course measure these or estimate these numerical gradients
[32:40] estimate these numerical gradients numerically just like we've seen before
[32:43] numerically just like we've seen before so if i take this expression
[32:45] so if i take this expression and i create a def lol function here
[32:49] and i create a def lol function here and put this here now the reason i'm
[32:51] and put this here now the reason i'm creating a gating function hello here is
[32:53] creating a gating function hello here is because i don't want to pollute or mess
[32:55] because i don't want to pollute or mess up the global scope here this is just
[32:57] up the global scope here this is just kind of like a little staging area and
[32:58] kind of like a little staging area and as you know in python all of these will
[33:00] as you know in python all of these will be local variables to this function so
[33:02] be local variables to this function so i'm not changing any of the global scope
[33:04] i'm not changing any of the global scope here
[33:05] here so here l1 will be l
[33:09] so here l1 will be l and then copy pasting this expression
[33:13] and then copy pasting this expression we're going to add a small amount h
[33:17] in for example a
[33:20] in for example a right and this would be measuring the
[33:22] right and this would be measuring the derivative of l with respect to a
[33:25] derivative of l with respect to a so here this will be l2
[33:28] so here this will be l2 and then we want to print this
[33:29] and then we want to print this derivative so print
[33:31] derivative so print l2 minus l1 which is how much l changed
[33:35] l2 minus l1 which is how much l changed and then normalize it by h so this is
[33:37] and then normalize it by h so this is the rise over run
[33:39] the rise over run and we have to be careful because l is a
[33:41] and we have to be careful because l is a value node so we actually want its data
[33:45] value node so we actually want its data um
[33:46] um so that these are floats dividing by h
[33:48] so that these are floats dividing by h and this should print the derivative of
[33:50] and this should print the derivative of l with respect to a because a is the one
[33:53] l with respect to a because a is the one that we bumped a little bit by h
[33:55] that we bumped a little bit by h so what is the
[33:57] so what is the derivative of l with respect to a
[33:59] derivative of l with respect to a it's six
[34:01] it's six okay and obviously
[34:03] okay and obviously if we change l by h
[34:06] if we change l by h then that would be
[34:09] then that would be here effectively
[34:12] here effectively this looks really awkward but changing l
[34:14] this looks really awkward but changing l by h
[34:16] by h you see the derivative here is 1. um
[34:20] you see the derivative here is 1. um that's kind of like the base case of
[34:23] that's kind of like the base case of what we are doing here
[34:24] what we are doing here so basically we cannot come up here and
[34:26] so basically we cannot come up here and we can manually set l.grad to one this
[34:29] we can manually set l.grad to one this is our manual back propagation
[34:31] is our manual back propagation l dot grad is one and let's redraw
[34:35] l dot grad is one and let's redraw and we'll see that we filled in grad as
[34:37] and we'll see that we filled in grad as 1 for l
[34:39] 1 for l we're now going to continue the back
[34:40] we're now going to continue the back propagation so let's here look at the
[34:42] propagation so let's here look at the derivatives of l with respect to d and f
[34:45] derivatives of l with respect to d and f let's do a d first
[34:47] let's do a d first so what we are interested in if i create
[34:49] so what we are interested in if i create a markdown on here is we'd like to know
[34:51] a markdown on here is we'd like to know basically we have that l is d times f
[34:54] basically we have that l is d times f and we'd like to know what is uh d
[34:57] and we'd like to know what is uh d l by d d
[35:00] l by d d what is that
[35:01] what is that and if you know your calculus uh l is d
[35:03] and if you know your calculus uh l is d times f so what is d l by d d it would
[35:06] times f so what is d l by d d it would be f
[35:08] be f and if you don't believe me we can also
[35:10] and if you don't believe me we can also just derive it because the proof would
[35:11] just derive it because the proof would be fairly straightforward uh we go to
[35:14] be fairly straightforward uh we go to the
[35:15] the definition of the derivative which is f
[35:18] definition of the derivative which is f of x plus h minus f of x divide h
[35:22] of x plus h minus f of x divide h as a limit limit of h goes to zero of
[35:24] as a limit limit of h goes to zero of this kind of expression so when we have
[35:26] this kind of expression so when we have l is d times f
[35:28] l is d times f then increasing d by h
[35:31] then increasing d by h would give us the output of b plus h
[35:33] would give us the output of b plus h times f
[35:35] times f that's basically f of x plus h right
[35:38] that's basically f of x plus h right minus d times f
[35:42] minus d times f and then divide h and symbolically
[35:44] and then divide h and symbolically expanding out here we would have
[35:46] expanding out here we would have basically d times f plus h times f minus
[35:49] basically d times f plus h times f minus t times f divide h
[35:52] t times f divide h and then you see how the df minus df
[35:54] and then you see how the df minus df cancels so you're left with h times f
[35:57] cancels so you're left with h times f divide h
[35:58] divide h which is f
[35:59] which is f so in the limit as h goes to zero of
[36:03] so in the limit as h goes to zero of you know
[36:04] you know derivative
[36:06] derivative definition we just get f in the case of
[36:09] definition we just get f in the case of d times f
[36:12] d times f so
[36:13] so symmetrically
[36:14] symmetrically dl by d
[36:15] dl by d f will just be d
[36:18] f will just be d so what we have is that f dot grad
[36:21] so what we have is that f dot grad we see now is just the value of d
[36:24] we see now is just the value of d which is 4.
[36:28] and we see that d dot grad
[36:31] d dot grad is just uh the value of f
[36:36] and so the value of f is negative two
[36:41] and so the value of f is negative two so we'll set those manually
[36:45] let me erase this markdown node and then let's redraw what we have
[36:50] okay and let's just make sure that these were
[36:53] and let's just make sure that these were correct so we seem to think that dl by
[36:56] correct so we seem to think that dl by dd is negative two so let's double check
[36:59] dd is negative two so let's double check um let me erase this plus h from before
[37:02] um let me erase this plus h from before and now we want the derivative with
[37:03] and now we want the derivative with respect to f
[37:05] respect to f so let's just come here when i create f
[37:06] so let's just come here when i create f and let's do a plus h here and this
[37:08] and let's do a plus h here and this should print the derivative of l with
[37:10] should print the derivative of l with respect to f so we expect to see four
[37:14] respect to f so we expect to see four yeah and this is four up to floating
[37:16] yeah and this is four up to floating point
[37:17] point funkiness
[37:18] funkiness and then dl by dd
[37:21] and then dl by dd should be f which is negative two
[37:25] should be f which is negative two grad is negative two
[37:26] grad is negative two so if we again come here and we change d
[37:31] d dot data plus equals h right here
[37:35] d dot data plus equals h right here so we expect so we've added a little h
[37:37] so we expect so we've added a little h and then we see how l changed and we
[37:40] and then we see how l changed and we expect to print
[37:42] expect to print uh negative two
[37:44] uh negative two there we go
[37:47] so we've numerically verified what we're doing here is what kind of like an
[37:50] doing here is what kind of like an inline gradient check gradient check is
[37:53] inline gradient check gradient check is when we
[37:54] when we are deriving this like back propagation
[37:56] are deriving this like back propagation and getting the derivative with respect
[37:57] and getting the derivative with respect to all the intermediate results and then
[38:00] to all the intermediate results and then numerical gradient is just you know
[38:03] numerical gradient is just you know estimating it using small step size
[38:06] estimating it using small step size now we're getting to the crux of
[38:08] now we're getting to the crux of backpropagation so this will be the most
[38:10] backpropagation so this will be the most important node to understand because if
[38:12] important node to understand because if you understand the gradient for this
[38:14] you understand the gradient for this node you understand all of back
[38:16] node you understand all of back propagation and all of training of
[38:17] propagation and all of training of neural nets basically
[38:19] neural nets basically so we need to derive dl by bc
[38:23] so we need to derive dl by bc in other words the derivative of l with
[38:24] in other words the derivative of l with respect to c
[38:26] respect to c because we've computed all these other
[38:27] because we've computed all these other gradients already
[38:29] gradients already now we're coming here and we're
[38:30] now we're coming here and we're continuing the back propagation manually
[38:33] continuing the back propagation manually so we want dl by dc and then we'll also
[38:36] so we want dl by dc and then we'll also derive dl by de
[38:38] derive dl by de now here's the problem
[38:40] now here's the problem how do we derive dl
[38:41] how do we derive dl by dc
[38:44] by dc we actually know the derivative l with
[38:46] we actually know the derivative l with respect to d so we know how l assessed
[38:48] respect to d so we know how l assessed it to d
[38:50] it to d but how is l sensitive to c so if we
[38:53] but how is l sensitive to c so if we wiggle c how does that impact l
[38:55] wiggle c how does that impact l through d
[38:58] through d so we know dl by dc
[39:01] and we also here know how c impacts d
[39:04] and we also here know how c impacts d and so just very intuitively if you know
[39:06] and so just very intuitively if you know the impact that c is having on d and the
[39:09] the impact that c is having on d and the impact that d is having on l
[39:11] impact that d is having on l then you should be able to somehow put
[39:12] then you should be able to somehow put that information together to figure out
[39:14] that information together to figure out how c impacts l
[39:16] how c impacts l and indeed this is what we can actually
[39:18] and indeed this is what we can actually do so in particular we know just
[39:20] do so in particular we know just concentrating on d first let's look at
[39:22] concentrating on d first let's look at how what is the derivative basically of
[39:24] how what is the derivative basically of d with respect to c so in other words
[39:27] d with respect to c so in other words what is dd by dc
[39:31] so here we know that d is c times c plus
[39:34] so here we know that d is c times c plus e
[39:35] e that's what we know and now we're
[39:37] that's what we know and now we're interested in dd by dc
[39:39] interested in dd by dc if you just know your calculus again and
[39:41] if you just know your calculus again and you remember that differentiating c plus
[39:43] you remember that differentiating c plus e with respect to c you know that that
[39:45] e with respect to c you know that that gives you
[39:46] gives you 1.0
[39:47] 1.0 and we can also go back to the basics
[39:49] and we can also go back to the basics and derive this because again we can go
[39:51] and derive this because again we can go to our f of x plus h minus f of x
[39:54] to our f of x plus h minus f of x divide by h
[39:56] divide by h that's the definition of a derivative as
[39:58] that's the definition of a derivative as h goes to zero
[40:00] h goes to zero and so here
[40:01] and so here focusing on c and its effect on d
[40:04] focusing on c and its effect on d we can basically do the f of x plus h
[40:06] we can basically do the f of x plus h will be
[40:07] will be c is incremented by h plus e
[40:10] c is incremented by h plus e that's the first evaluation of our
[40:12] that's the first evaluation of our function minus
[40:14] function minus c plus e
[40:16] c plus e and then divide h
[40:18] and then divide h and so what is this
[40:19] and so what is this uh just expanding this out this will be
[40:21] uh just expanding this out this will be c plus h plus e minus c minus e
[40:25] c plus h plus e minus c minus e divide h and then you see here how c
[40:27] divide h and then you see here how c minus c cancels e minus e cancels we're
[40:30] minus c cancels e minus e cancels we're left with h over h which is 1.0
[40:33] left with h over h which is 1.0 and so
[40:35] and so by symmetry also d d by d
[40:38] by symmetry also d d by d e
[40:39] e will be 1.0 as well
[40:42] will be 1.0 as well so basically the derivative of a sum
[40:44] so basically the derivative of a sum expression is very simple and and this
[40:46] expression is very simple and and this is the local derivative so i call this
[40:49] is the local derivative so i call this the local derivative because we have the
[40:51] the local derivative because we have the final output value all the way at the
[40:52] final output value all the way at the end of this graph and we're now like a
[40:54] end of this graph and we're now like a small node here
[40:55] small node here and this is a little plus node
[40:58] and this is a little plus node and it the little plus node doesn't know
[41:00] and it the little plus node doesn't know anything about the rest of the graph
[41:02] anything about the rest of the graph that it's embedded in all it knows is
[41:04] that it's embedded in all it knows is that it did a plus it took a c and an e
[41:07] that it did a plus it took a c and an e added them and created d
[41:09] added them and created d and this plus note also knows the local
[41:11] and this plus note also knows the local influence of c on d or rather rather the
[41:14] influence of c on d or rather rather the derivative of d with respect to c and it
[41:16] derivative of d with respect to c and it also
[41:17] also knows the derivative of d with respect
[41:18] knows the derivative of d with respect to e but that's not what we want that's
[41:21] to e but that's not what we want that's just a local derivative what we actually
[41:23] just a local derivative what we actually want is d l by d c and l could l is here
[41:27] want is d l by d c and l could l is here just one step away but in a general case
[41:30] just one step away but in a general case this little plus note is could be
[41:32] this little plus note is could be embedded in like a massive graph
[41:34] embedded in like a massive graph so
[41:35] so again we know how l impacts d and now we
[41:38] again we know how l impacts d and now we know how c and e impact d how do we put
[41:41] know how c and e impact d how do we put that information together to write dl by
[41:43] that information together to write dl by dc and the answer of course is the chain
[41:46] dc and the answer of course is the chain rule in calculus
[41:47] rule in calculus and so um
[41:50] and so um i pulled up a chain rule here from
[41:51] i pulled up a chain rule here from kapedia
[41:52] kapedia and
[41:53] and i'm going to go through this very
[41:54] i'm going to go through this very briefly so chain rule
[41:57] briefly so chain rule wikipedia sometimes can be very
[41:58] wikipedia sometimes can be very confusing and calculus can
[42:00] confusing and calculus can can be very confusing like this is the
[42:02] can be very confusing like this is the way i
[42:03] way i learned
[42:05] learned chain rule and it was very confusing
[42:06] chain rule and it was very confusing like what is happening it's just
[42:08] like what is happening it's just complicated so i like this expression
[42:10] complicated so i like this expression much better
[42:12] much better if a variable z depends on a variable y
[42:15] if a variable z depends on a variable y which itself depends on the variable x
[42:18] which itself depends on the variable x then z depends on x as well obviously
[42:20] then z depends on x as well obviously through the intermediate variable y
[42:22] through the intermediate variable y in this case the chain rule is expressed
[42:24] in this case the chain rule is expressed as
[42:25] as if you want dz by dx
[42:28] if you want dz by dx then you take the dz by dy and you
[42:30] then you take the dz by dy and you multiply it by d y by dx
[42:33] multiply it by d y by dx so the chain rule fundamentally is
[42:34] so the chain rule fundamentally is telling you
[42:36] telling you how
[42:37] how we chain these
[42:39] we chain these uh derivatives together
[42:41] uh derivatives together correctly so to differentiate through a
[42:44] correctly so to differentiate through a function composition
[42:46] function composition we have to apply a multiplication
[42:48] we have to apply a multiplication of
[42:49] of those derivatives
[42:51] those derivatives so that's really what chain rule is
[42:53] so that's really what chain rule is telling us
[42:54] telling us and there's a nice little intuitive
[42:56] and there's a nice little intuitive explanation here which i also think is
[42:58] explanation here which i also think is kind of cute the chain rule says that
[42:59] kind of cute the chain rule says that knowing the instantaneous rate of change
[43:01] knowing the instantaneous rate of change of z with respect to y and y relative to
[43:03] of z with respect to y and y relative to x allows one to calculate the
[43:04] x allows one to calculate the instantaneous rate of change of z
[43:06] instantaneous rate of change of z relative to x
[43:07] relative to x as a product of those two rates of
[43:09] as a product of those two rates of change
[43:10] change simply the product of those two
[43:12] simply the product of those two so here's a good one
[43:14] so here's a good one if a car travels twice as fast as
[43:16] if a car travels twice as fast as bicycle and the bicycle is four times as
[43:18] bicycle and the bicycle is four times as fast as walking man
[43:19] fast as walking man then the car travels two times four
[43:22] then the car travels two times four eight times as fast as demand
[43:25] eight times as fast as demand and so this makes it very clear that the
[43:27] and so this makes it very clear that the correct thing to do sort of
[43:29] correct thing to do sort of is to multiply
[43:30] is to multiply so
[43:31] so cars twice as fast as bicycle and
[43:33] cars twice as fast as bicycle and bicycle is four times as fast as man
[43:36] bicycle is four times as fast as man so the car will be eight times as fast
[43:38] so the car will be eight times as fast as the man and so we can take these
[43:42] as the man and so we can take these intermediate rates of change if you will
[43:44] intermediate rates of change if you will and multiply them together
[43:46] and multiply them together and that justifies the
[43:48] and that justifies the chain rule intuitively so have a look at
[43:50] chain rule intuitively so have a look at chain rule about here really what it
[43:52] chain rule about here really what it means for us is there's a very simple
[43:54] means for us is there's a very simple recipe for deriving what we want which
[43:56] recipe for deriving what we want which is dl by dc
[43:59] is dl by dc and what we have so far
[44:01] and what we have so far is we know
[44:03] is we know want
[44:05] want and we know
[44:07] and we know what is the
[44:08] what is the impact of d on l so we know d l by
[44:12] impact of d on l so we know d l by d d the derivative of l with respect to
[44:14] d d the derivative of l with respect to d d we know that that's negative two
[44:17] d d we know that that's negative two and now because of this local
[44:19] and now because of this local reasoning that we've done here we know
[44:21] reasoning that we've done here we know dd by d
[44:23] dd by d c
[44:24] c so how does c impact d and in
[44:27] so how does c impact d and in particular this is a plus node so the
[44:29] particular this is a plus node so the local derivative is simply 1.0 it's very
[44:32] local derivative is simply 1.0 it's very simple
[44:33] simple and so
[44:34] and so the chain rule tells us that dl by dc
[44:37] the chain rule tells us that dl by dc going through this intermediate variable
[44:40] going through this intermediate variable will just be simply d l by
[44:43] will just be simply d l by d
[44:44] d times
[44:49] dd by dc that's chain rule
[44:53] that's chain rule so this is identical to what's happening
[44:55] so this is identical to what's happening here
[44:56] here except
[44:58] except z is rl
[44:59] z is rl y is our d and x is rc
[45:03] y is our d and x is rc so we literally just have to multiply
[45:05] so we literally just have to multiply these
[45:06] these and because
[45:10] these local derivatives like dd by dc are just one
[45:14] are just one we basically just copy over dl by dd
[45:17] we basically just copy over dl by dd because this is just times one
[45:19] because this is just times one so what does it do so because dl by dd
[45:22] so what does it do so because dl by dd is negative two what is dl by dc
[45:25] is negative two what is dl by dc well it's the local gradient 1.0 times
[45:29] well it's the local gradient 1.0 times dl by dd which is negative two
[45:31] dl by dd which is negative two so literally what a plus node does you
[45:33] so literally what a plus node does you can look at it that way is it literally
[45:35] can look at it that way is it literally just routes the gradient
[45:37] just routes the gradient because the plus nodes local derivatives
[45:39] because the plus nodes local derivatives are just one and so in the chain rule
[45:41] are just one and so in the chain rule one times
[45:43] one times dl by dd
[45:45] dl by dd is um
[45:47] is um is uh is just dl by dd and so that
[45:50] is uh is just dl by dd and so that derivative just gets routed to both c
[45:53] derivative just gets routed to both c and to e in this case
[45:55] and to e in this case so basically um we have that that grad
[45:59] so basically um we have that that grad or let's start with c since that's the
[46:01] or let's start with c since that's the one we looked at
[46:02] one we looked at is
[46:03] is negative two times one
[46:06] negative two times one negative two
[46:08] negative two and in the same way by symmetry e that
[46:11] and in the same way by symmetry e that grad will be negative two that's the
[46:13] grad will be negative two that's the claim so we can set those
[46:16] claim so we can set those we can redraw
[46:19] we can redraw and you see how we just assign negative
[46:20] and you see how we just assign negative to negative two so this backpropagating
[46:23] to negative two so this backpropagating signal which is carrying the information
[46:25] signal which is carrying the information of like what is the derivative of l with
[46:26] of like what is the derivative of l with respect to all the intermediate nodes
[46:28] respect to all the intermediate nodes we can imagine it almost like flowing
[46:30] we can imagine it almost like flowing backwards through the graph and a plus
[46:32] backwards through the graph and a plus node will simply distribute the
[46:34] node will simply distribute the derivative to all the leaf nodes sorry
[46:36] derivative to all the leaf nodes sorry to all the children nodes of it
[46:39] to all the children nodes of it so this is the claim and now let's
[46:40] so this is the claim and now let's verify it so let me remove the plus h
[46:43] verify it so let me remove the plus h here from before
[46:45] here from before and now instead what we're going to do
[46:46] and now instead what we're going to do is we're going to increment c so c dot
[46:48] is we're going to increment c so c dot data will be credited by h
[46:50] data will be credited by h and when i run this we expect to see
[46:52] and when i run this we expect to see negative 2
[46:54] negative 2 negative 2. and then of course for e
[46:58] negative 2. and then of course for e so e dot data plus equals h and we
[47:01] so e dot data plus equals h and we expect to see negative 2.
[47:03] expect to see negative 2. simple
[47:07] so those are the derivatives of these internal nodes
[47:11] internal nodes and now we're going to recurse our way
[47:13] and now we're going to recurse our way backwards again
[47:15] backwards again and we're again going to apply the chain
[47:17] and we're again going to apply the chain rule so here we go our second
[47:19] rule so here we go our second application of chain rule and we will
[47:20] application of chain rule and we will apply it all the way through the graph
[47:22] apply it all the way through the graph we just happen to only have one more
[47:24] we just happen to only have one more node remaining
[47:25] node remaining we have that d l
[47:27] we have that d l by d e
[47:28] by d e as we have just calculated is negative
[47:30] as we have just calculated is negative two so we know that
[47:32] two so we know that so we know the derivative of l with
[47:33] so we know the derivative of l with respect to e
[47:36] and now we want dl
[47:39] and now we want dl by
[47:40] by da
[47:41] da right
[47:42] right and the chain rule is telling us that
[47:44] and the chain rule is telling us that that's just dl by de
[47:48] negative 2 times the local gradient so what is the
[47:52] times the local gradient so what is the local gradient basically d e
[47:55] local gradient basically d e by d a
[47:56] by d a we have to look at that
[47:59] we have to look at that so i'm a little times node
[48:02] so i'm a little times node inside a massive graph
[48:04] inside a massive graph and i only know that i did a times b and
[48:06] and i only know that i did a times b and i produced an e
[48:09] i produced an e so now what is d e by d a and d e by d b
[48:12] so now what is d e by d a and d e by d b that's the only thing that i sort of
[48:14] that's the only thing that i sort of know about that's my local gradient
[48:17] know about that's my local gradient so
[48:17] so because we have that e's a times b we're
[48:20] because we have that e's a times b we're asking what is d e by d a
[48:24] asking what is d e by d a and of course we just did that here we
[48:26] and of course we just did that here we had a
[48:27] had a times so i'm not going to rederive it
[48:30] times so i'm not going to rederive it but if you want to differentiate this
[48:32] but if you want to differentiate this with respect to a you'll just get b
[48:34] with respect to a you'll just get b right the value of b
[48:36] right the value of b which in this case is negative 3.0
[48:41] so basically we have that dl by da
[48:45] basically we have that dl by da well let me just do it right here we
[48:47] well let me just do it right here we have that a dot grad and we are applying
[48:49] have that a dot grad and we are applying chain rule here
[48:50] chain rule here is d l by d e which we see here is
[48:54] is d l by d e which we see here is negative two
[48:56] negative two times
[48:57] times what is d e by d a
[48:59] what is d e by d a it's the value of b which is negative 3.
[49:04] that's it
[49:07] and then we have b grad is again dl by
[49:10] and then we have b grad is again dl by de
[49:11] de which is negative 2
[49:13] which is negative 2 just the same way
[49:14] just the same way times
[49:15] times what is d e by d
[49:18] what is d e by d um db
[49:19] um db is the value of a which is 2.2.0
[49:23] is the value of a which is 2.2.0 as the value of a
[49:25] as the value of a so these are our claimed derivatives
[49:28] so these are our claimed derivatives let's
[49:30] let's redraw
[49:32] redraw and we see here that
[49:33] and we see here that a dot grad turns out to be 6 because
[49:36] a dot grad turns out to be 6 because that is negative 2 times negative 3
[49:38] that is negative 2 times negative 3 and b dot grad is negative 4
[49:41] and b dot grad is negative 4 times sorry is negative 2 times 2 which
[49:43] times sorry is negative 2 times 2 which is negative 4.
[49:45] is negative 4. so those are our claims let's delete
[49:47] so those are our claims let's delete this and let's verify them
[49:50] this and let's verify them we have
[49:52] we have a here a dot data plus equals h
[49:57] so the claim is that a dot grad is six
[50:01] a dot grad is six let's verify
[50:03] let's verify six
[50:04] six and we have beta data
[50:07] and we have beta data plus equals h
[50:08] plus equals h so nudging b by h
[50:11] so nudging b by h and looking at what happens
[50:13] and looking at what happens we claim it's negative four
[50:15] we claim it's negative four and indeed it's negative four plus minus
[50:17] and indeed it's negative four plus minus again float oddness
[50:20] again float oddness um
[50:21] um and uh
[50:23] and uh that's it this
[50:24] that's it this that was the manual
[50:26] that was the manual back propagation
[50:28] back propagation uh all the way from here to all the leaf
[50:30] uh all the way from here to all the leaf nodes and we've done it piece by piece
[50:33] nodes and we've done it piece by piece and really all we've done is as you saw
[50:35] and really all we've done is as you saw we iterated through all the nodes one by
[50:37] we iterated through all the nodes one by one and locally applied the chain rule
[50:39] one and locally applied the chain rule we always know what is the derivative of
[50:41] we always know what is the derivative of l with respect to this little output and
[50:44] l with respect to this little output and then we look at how this output was
[50:45] then we look at how this output was produced this output was produced
[50:47] produced this output was produced through some operation and we have the
[50:49] through some operation and we have the pointers to the children nodes of this
[50:51] pointers to the children nodes of this operation
[50:52] operation and so in this little operation we know
[50:54] and so in this little operation we know what the local derivatives are and we
[50:56] what the local derivatives are and we just multiply them onto the derivative
[50:58] just multiply them onto the derivative always
[50:59] always so we just go through and recursively
[51:01] so we just go through and recursively multiply on the local derivatives and
[51:04] multiply on the local derivatives and that's what back propagation is is just
[51:05] that's what back propagation is is just a recursive application of chain rule
[51:08] a recursive application of chain rule backwards through the computation graph
[51:10] backwards through the computation graph let's see this power in action just very
[51:12] let's see this power in action just very briefly what we're going to do is we're
[51:14] briefly what we're going to do is we're going to
[51:15] going to nudge our inputs to try to make l go up
[51:19] nudge our inputs to try to make l go up so in particular what we're doing is we
[51:21] so in particular what we're doing is we want a.data we're going to change it
[51:24] want a.data we're going to change it and if we want l to go up that means we
[51:26] and if we want l to go up that means we just have to go in the direction of the
[51:27] just have to go in the direction of the gradient so
[51:29] gradient so a
[51:30] a should increase in the direction of
[51:32] should increase in the direction of gradient by like some small step amount
[51:34] gradient by like some small step amount this is the step size
[51:36] this is the step size and we don't just want this for ba but
[51:38] and we don't just want this for ba but also for b
[51:41] also for c
[51:44] also for c also for f
[51:46] also for f those are
[51:47] those are leaf nodes which we usually have control
[51:49] leaf nodes which we usually have control over
[51:50] over and if we nudge in direction of the
[51:52] and if we nudge in direction of the gradient we expect a positive influence
[51:54] gradient we expect a positive influence on l
[51:55] on l so we expect l to go up
[51:58] so we expect l to go up positively
[51:59] positively so it should become less negative it
[52:01] so it should become less negative it should go up to say negative you know
[52:03] should go up to say negative you know six or something like that
[52:05] six or something like that uh it's hard to tell exactly and we'd
[52:08] uh it's hard to tell exactly and we'd have to rewrite the forward pass so let
[52:09] have to rewrite the forward pass so let me just um
[52:12] me just um do that here
[52:13] do that here um
[52:16] this would be the forward pass f would be unchanged this is effectively the
[52:20] be unchanged this is effectively the forward pass and now if we print l.data
[52:24] forward pass and now if we print l.data we expect because we nudged all the
[52:27] we expect because we nudged all the values all the inputs in the rational
[52:28] values all the inputs in the rational gradient we expected a less negative l
[52:30] gradient we expected a less negative l we expect it to go up
[52:32] we expect it to go up so maybe it's negative six or so let's
[52:34] so maybe it's negative six or so let's see what happens
[52:36] see what happens okay negative seven
[52:38] okay negative seven and uh this is basically one step of an
[52:41] and uh this is basically one step of an optimization that we'll end up running
[52:43] optimization that we'll end up running and really does gradient just give us
[52:46] and really does gradient just give us some power because we know how to
[52:47] some power because we know how to influence the final outcome and this
[52:49] influence the final outcome and this will be extremely useful for training
[52:50] will be extremely useful for training knowledge as well as you'll see
[52:52] knowledge as well as you'll see so now i would like to do one more uh
[52:55] so now i would like to do one more uh example of manual backpropagation using
[52:58] example of manual backpropagation using a bit more complex and uh useful example
[53:02] a bit more complex and uh useful example we are going to back propagate through a
[53:04] we are going to back propagate through a neuron
[53:05] neuron so
[53:07] so we want to eventually build up neural
[53:08] we want to eventually build up neural networks and in the simplest case these
[53:10] networks and in the simplest case these are multilateral perceptrons as they're
[53:12] are multilateral perceptrons as they're called so this is a two layer neural net
[53:15] called so this is a two layer neural net and it's got these hidden layers made up
[53:17] and it's got these hidden layers made up of neurons and these neurons are fully
[53:18] of neurons and these neurons are fully connected to each other
[53:20] connected to each other now biologically neurons are very
[53:21] now biologically neurons are very complicated devices but we have very
[53:23] complicated devices but we have very simple mathematical models of them
[53:26] simple mathematical models of them and so this is a very simple
[53:27] and so this is a very simple mathematical model of a neuron you have
[53:29] mathematical model of a neuron you have some inputs axis
[53:31] some inputs axis and then you have these synapses that
[53:33] and then you have these synapses that have weights on them so
[53:36] have weights on them so the w's are weights
[53:39] the w's are weights and then
[53:40] and then the synapse interacts with the input to
[53:42] the synapse interacts with the input to this neuron multiplicatively so what
[53:44] this neuron multiplicatively so what flows to the cell body
[53:47] flows to the cell body of this neuron is w times x
[53:49] of this neuron is w times x but there's multiple inputs so there's
[53:51] but there's multiple inputs so there's many w times x's flowing into the cell
[53:53] many w times x's flowing into the cell body
[53:54] body the cell body then has also like some
[53:56] the cell body then has also like some bias
[53:57] bias so this is kind of like the
[53:59] so this is kind of like the inert innate sort of trigger happiness
[54:02] inert innate sort of trigger happiness of this neuron so this bias can make it
[54:04] of this neuron so this bias can make it a bit more trigger happy or a bit less
[54:06] a bit more trigger happy or a bit less trigger happy regardless of the input
[54:08] trigger happy regardless of the input but basically we're taking all the w
[54:10] but basically we're taking all the w times x
[54:11] times x of all the inputs adding the bias and
[54:13] of all the inputs adding the bias and then we take it through an activation
[54:15] then we take it through an activation function
[54:16] function and this activation function is usually
[54:18] and this activation function is usually some kind of a squashing function
[54:20] some kind of a squashing function like a sigmoid or 10h or something like
[54:22] like a sigmoid or 10h or something like that so as an example
[54:24] that so as an example we're going to use the 10h in this
[54:26] we're going to use the 10h in this example
[54:28] example numpy has a
[54:29] numpy has a np.10h
[54:31] np.10h so
[54:32] so we can call it on a range
[54:34] we can call it on a range and we can plot it
[54:36] and we can plot it this is the 10h function and you see
[54:38] this is the 10h function and you see that the inputs as they come in
[54:41] that the inputs as they come in get squashed on the y coordinate here so
[54:44] get squashed on the y coordinate here so um
[54:45] um right at zero we're going to get exactly
[54:47] right at zero we're going to get exactly zero and then as you go more positive in
[54:49] zero and then as you go more positive in the input
[54:50] the input then you'll see that the function will
[54:52] then you'll see that the function will only go up to one and then plateau out
[54:55] only go up to one and then plateau out and so if you pass in very positive
[54:57] and so if you pass in very positive inputs we're gonna cap it smoothly at
[55:00] inputs we're gonna cap it smoothly at one and on the negative side we're gonna
[55:02] one and on the negative side we're gonna cap it smoothly to negative one
[55:04] cap it smoothly to negative one so that's 10h
[55:06] so that's 10h and that's the squashing function or an
[55:08] and that's the squashing function or an activation function and what comes out
[55:10] activation function and what comes out of this neuron is just the activation
[55:12] of this neuron is just the activation function applied to the dot product of
[55:14] function applied to the dot product of the weights and the
[55:16] the weights and the inputs
[55:18] inputs so let's
[55:19] so let's write one out
[55:21] write one out um
[55:22] um i'm going to copy paste because
[55:27] i don't want to type too much but okay so here we have the inputs
[55:31] but okay so here we have the inputs x1 x2 so this is a two-dimensional
[55:33] x1 x2 so this is a two-dimensional neuron so two inputs are going to come
[55:34] neuron so two inputs are going to come in
[55:35] in these are thought out as the weights of
[55:37] these are thought out as the weights of this neuron
[55:38] this neuron weights w1 w2 and these weights again
[55:41] weights w1 w2 and these weights again are the synaptic strengths for each
[55:43] are the synaptic strengths for each input
[55:45] input and this is the bias of the neuron
[55:47] and this is the bias of the neuron b
[55:49] b and now we want to do is according to
[55:51] and now we want to do is according to this model we need to multiply x1 times
[55:54] this model we need to multiply x1 times w1
[55:55] w1 and x2 times w2
[55:57] and x2 times w2 and then we need to add bias on top of
[56:00] and then we need to add bias on top of it
[56:01] it and it gets a little messy here but all
[56:03] and it gets a little messy here but all we are trying to do is x1 w1 plus x2 w2
[56:06] we are trying to do is x1 w1 plus x2 w2 plus b
[56:07] plus b and these are multiply here
[56:09] and these are multiply here except i'm doing it in small steps so
[56:12] except i'm doing it in small steps so that we actually have pointers to all
[56:13] that we actually have pointers to all these intermediate nodes so we have x1
[56:15] these intermediate nodes so we have x1 w1 variable x times x2 w2 variable and
[56:19] w1 variable x times x2 w2 variable and i'm also labeling them
[56:21] i'm also labeling them so n is now
[56:23] so n is now the cell body raw
[56:25] the cell body raw raw
[56:26] raw activation without
[56:28] activation without the activation function for now
[56:30] the activation function for now and this should be enough to basically
[56:32] and this should be enough to basically plot it so draw dot of n
[56:37] gives us x1 times w1 x2 times w2
[56:41] gives us x1 times w1 x2 times w2 being added
[56:43] being added then the bias gets added on top of this
[56:45] then the bias gets added on top of this and this n
[56:47] and this n is this sum
[56:49] is this sum so we're now going to take it through an
[56:50] so we're now going to take it through an activation function
[56:52] activation function and let's say we use the 10h
[56:54] and let's say we use the 10h so that we produce the output
[56:56] so that we produce the output so what we'd like to do here is we'd
[56:58] so what we'd like to do here is we'd like to do the output and i'll call it o
[57:01] like to do the output and i'll call it o is um
[57:03] is um n dot 10h
[57:05] n dot 10h okay but we haven't yet written the 10h
[57:08] okay but we haven't yet written the 10h now the reason that we need to implement
[57:09] now the reason that we need to implement another 10h function here is that
[57:12] another 10h function here is that tanh is a
[57:14] tanh is a hyperbolic function and we've only so
[57:16] hyperbolic function and we've only so far implemented a plus and the times and
[57:18] far implemented a plus and the times and you can't make a 10h out of just pluses
[57:20] you can't make a 10h out of just pluses and times
[57:22] and times you also need exponentiation so 10h is
[57:25] you also need exponentiation so 10h is this kind of a formula here
[57:27] this kind of a formula here you can use either one of these and you
[57:28] you can use either one of these and you see that there's exponentiation involved
[57:30] see that there's exponentiation involved which we have not implemented yet for
[57:32] which we have not implemented yet for our low value node here so we're not
[57:34] our low value node here so we're not going to be able to produce 10h yet and
[57:36] going to be able to produce 10h yet and we have to go back up and implement
[57:37] we have to go back up and implement something like it
[57:39] something like it now one option here
[57:42] now one option here is we could actually implement um
[57:44] is we could actually implement um exponentiation
[57:46] exponentiation right and we could return the x of a
[57:49] right and we could return the x of a value instead of a 10h of a value
[57:52] value instead of a 10h of a value because if we had x then we have
[57:54] because if we had x then we have everything else that we need so um
[57:56] everything else that we need so um because we know how to add and we know
[57:58] because we know how to add and we know how to
[58:00] how to um
[58:01] um we know how to add and we know how to
[58:02] we know how to add and we know how to multiply so we'd be able to create 10h
[58:04] multiply so we'd be able to create 10h if we knew how to x
[58:06] if we knew how to x but for the purposes of this example i
[58:08] but for the purposes of this example i specifically wanted to
[58:10] specifically wanted to show you
[58:11] show you that we don't necessarily need to have
[58:13] that we don't necessarily need to have the most atomic pieces
[58:15] the most atomic pieces in
[58:16] in um
[58:16] um in this value object we can actually
[58:19] in this value object we can actually like create functions at arbitrary
[58:23] like create functions at arbitrary points of abstraction they can be
[58:24] points of abstraction they can be complicated functions but they can be
[58:26] complicated functions but they can be also very very simple functions like a
[58:27] also very very simple functions like a plus and it's totally up to us the only
[58:30] plus and it's totally up to us the only thing that matters is that we know how
[58:31] thing that matters is that we know how to differentiate through any one
[58:33] to differentiate through any one function so we take some inputs and we
[58:35] function so we take some inputs and we make an output the only thing that
[58:37] make an output the only thing that matters it can be arbitrarily complex
[58:38] matters it can be arbitrarily complex function as long as you know how to
[58:41] function as long as you know how to create the local derivative if you know
[58:43] create the local derivative if you know the local derivative of how the inputs
[58:44] the local derivative of how the inputs impact the output then that's all you
[58:46] impact the output then that's all you need so we're going to cluster up
[58:49] need so we're going to cluster up all of this expression and we're not
[58:51] all of this expression and we're not going to break it down to its atomic
[58:52] going to break it down to its atomic pieces we're just going to directly
[58:54] pieces we're just going to directly implement tanh
[58:55] implement tanh so let's do that
[58:57] so let's do that depth nh
[58:59] depth nh and then out will be a value
[59:02] and then out will be a value of
[59:03] of and we need this expression here so
[59:05] and we need this expression here so um
[59:08] let me actually copy paste
[59:14] let's grab n which is a cell.theta
[59:17] let's grab n which is a cell.theta and then this
[59:18] and then this i believe is the tan h
[59:21] i believe is the tan h math.x of
[59:24] math.x of two
[59:25] two no n
[59:27] no n n minus one over
[59:28] n minus one over two n plus one
[59:30] two n plus one maybe i can call this x
[59:33] maybe i can call this x just so that it matches exactly
[59:35] just so that it matches exactly okay and now
[59:37] okay and now this will be t
[59:40] this will be t and uh children of this node there's
[59:42] and uh children of this node there's just one child
[59:44] just one child and i'm wrapping it in a tuple so this
[59:46] and i'm wrapping it in a tuple so this is a tuple of one object just self
[59:48] is a tuple of one object just self and here the name of this operation will
[59:50] and here the name of this operation will be 10h
[59:52] be 10h and we're going to return that
[59:56] okay so now valley should be implementing 10h
[60:01] so now valley should be implementing 10h and now we can scroll all the way down
[60:03] and now we can scroll all the way down here
[60:04] here and we can actually do n.10 h and that's
[60:06] and we can actually do n.10 h and that's going to return the tanhd
[60:09] going to return the tanhd output of n
[60:11] output of n and now we should be able to draw it out
[60:12] and now we should be able to draw it out of o not of n
[60:14] of o not of n so let's see how that worked
[60:18] there we go n went through 10 h
[60:21] n went through 10 h to produce this output
[60:24] to produce this output so now tan h is a
[60:26] so now tan h is a sort of
[60:27] sort of our little micro grad supported node
[60:30] our little micro grad supported node here as an operation
[60:33] here as an operation and as long as we know the derivative of
[60:35] and as long as we know the derivative of 10h
[60:36] 10h then we'll be able to back propagate
[60:37] then we'll be able to back propagate through it now let's see this 10h in
[60:39] through it now let's see this 10h in action currently it's not squashing too
[60:41] action currently it's not squashing too much because the input to it is pretty
[60:43] much because the input to it is pretty low so if the bias was increased to say
[60:46] low so if the bias was increased to say eight
[60:49] eight then we'll see that what's flowing into
[60:51] then we'll see that what's flowing into the 10h now is
[60:53] the 10h now is two
[60:54] two and 10h is squashing it to 0.96 so we're
[60:57] and 10h is squashing it to 0.96 so we're already hitting the tail of this 10h and
[60:59] already hitting the tail of this 10h and it will sort of smoothly go up to 1 and
[61:01] it will sort of smoothly go up to 1 and then plateau out over there
[61:03] then plateau out over there okay so now i'm going to do something
[61:04] okay so now i'm going to do something slightly strange i'm going to change
[61:06] slightly strange i'm going to change this bias from 8 to this number
[61:09] this bias from 8 to this number 6.88 etc
[61:11] 6.88 etc and i'm going to do this for specific
[61:13] and i'm going to do this for specific reasons because we're about to start
[61:15] reasons because we're about to start back propagation
[61:16] back propagation and i want to make sure that our numbers
[61:19] and i want to make sure that our numbers come out nice they're not like very
[61:21] come out nice they're not like very crazy numbers they're nice numbers that
[61:22] crazy numbers they're nice numbers that we can sort of understand in our head
[61:24] we can sort of understand in our head let me also add a pose label
[61:26] let me also add a pose label o is short for output here
[61:29] o is short for output here so that's zero
[61:31] so that's zero okay so
[61:32] okay so 0.88 flows into 10 h comes out 0.7 so on
[61:36] 0.88 flows into 10 h comes out 0.7 so on so now we're going to do back
[61:37] so now we're going to do back propagation and we're going to fill in
[61:38] propagation and we're going to fill in all the gradients
[61:40] all the gradients so what is the derivative o with respect
[61:43] so what is the derivative o with respect to
[61:44] to all the
[61:45] all the inputs here and of course in the typical
[61:47] inputs here and of course in the typical neural network setting what we really
[61:48] neural network setting what we really care about the most is the derivative of
[61:51] care about the most is the derivative of these neurons on the weights
[61:53] these neurons on the weights specifically the w2 and w1 because those
[61:56] specifically the w2 and w1 because those are the weights that we're going to be
[61:57] are the weights that we're going to be changing part of the optimization
[61:59] changing part of the optimization and the other thing that we have to
[62:00] and the other thing that we have to remember is here we have only a single
[62:02] remember is here we have only a single neuron but in the neural natives
[62:03] neuron but in the neural natives typically have many neurons and they're
[62:04] typically have many neurons and they're connected
[62:07] connected so this is only like a one small neuron
[62:09] so this is only like a one small neuron a piece of a much bigger puzzle and
[62:10] a piece of a much bigger puzzle and eventually there's a loss function that
[62:12] eventually there's a loss function that sort of measures the accuracy of the
[62:13] sort of measures the accuracy of the neural net and we're back propagating
[62:15] neural net and we're back propagating with respect to that accuracy and trying
[62:16] with respect to that accuracy and trying to increase it
[62:19] to increase it so let's start off by propagation here
[62:21] so let's start off by propagation here in the end
[62:22] in the end what is the derivative of o with respect
[62:24] what is the derivative of o with respect to o the base case sort of we know
[62:26] to o the base case sort of we know always is that the gradient is just 1.0
[62:30] always is that the gradient is just 1.0 so let me fill it in
[62:32] so let me fill it in and then let me
[62:35] and then let me split out
[62:37] split out the drawing function
[62:40] the drawing function here
[62:43] and then here cell
[62:47] clear this output here okay
[62:50] clear this output here okay so now when we draw o we'll see that oh
[62:52] so now when we draw o we'll see that oh that grad is one
[62:53] that grad is one so now we're going to back propagate
[62:55] so now we're going to back propagate through the tan h
[62:56] through the tan h so to back propagate through 10h we need
[62:58] so to back propagate through 10h we need to know the local derivative of 10h
[63:01] to know the local derivative of 10h so if we have that
[63:03] so if we have that o is 10 h of
[63:07] o is 10 h of n
[63:08] n then what is d o by d n
[63:11] then what is d o by d n now what you could do is you could come
[63:13] now what you could do is you could come here and you could take this expression
[63:15] here and you could take this expression and you could
[63:16] and you could do your calculus derivative taking
[63:19] do your calculus derivative taking um and that would work but we can also
[63:21] um and that would work but we can also just scroll down wikipedia here
[63:23] just scroll down wikipedia here into a section that hopefully tells us
[63:26] into a section that hopefully tells us that derivative uh
[63:28] that derivative uh d by dx of 10 h of x is
[63:31] d by dx of 10 h of x is any of these i like this one 1 minus 10
[63:33] any of these i like this one 1 minus 10 h square of x
[63:35] h square of x so this is 1 minus 10 h
[63:37] so this is 1 minus 10 h of x squared
[63:39] of x squared so basically what this is saying is that
[63:41] so basically what this is saying is that d o by d n
[63:43] d o by d n is
[63:44] is 1 minus 10 h
[63:47] 1 minus 10 h of n
[63:48] of n squared
[63:51] squared and we already have 10 h of n that's
[63:52] and we already have 10 h of n that's just o
[63:54] just o so it's one minus o squared
[63:56] so it's one minus o squared so o is the output here so the output is
[63:59] so o is the output here so the output is this number
[64:02] this number data
[64:04] data is this number
[64:06] is this number and then
[64:08] and then what this is saying is that do by dn is
[64:10] what this is saying is that do by dn is 1 minus
[64:11] 1 minus this squared so
[64:13] this squared so one minus of that data squared
[64:16] one minus of that data squared is 0.5 conveniently
[64:18] is 0.5 conveniently so the local derivative of this 10 h
[64:21] so the local derivative of this 10 h operation here is 0.5
[64:24] operation here is 0.5 and
[64:25] and so that would be d o by d n
[64:27] so that would be d o by d n so
[64:28] so we can fill in that in that grad
[64:33] is 0.5 we'll just fill in
[64:42] so this is exactly 0.5 one half
[64:45] so this is exactly 0.5 one half so now we're going to continue the back
[64:47] so now we're going to continue the back propagation
[64:49] propagation this is 0.5 and this is a plus node
[64:52] this is 0.5 and this is a plus node so how is backprop going to what is that
[64:55] so how is backprop going to what is that going to do here
[64:56] going to do here and if you remember our previous example
[64:58] and if you remember our previous example a plus is just a distributor of gradient
[65:01] a plus is just a distributor of gradient so this gradient will simply flow to
[65:03] so this gradient will simply flow to both of these equally and that's because
[65:05] both of these equally and that's because the local derivative of this operation
[65:07] the local derivative of this operation is one for every one of its nodes so 1
[65:10] is one for every one of its nodes so 1 times 0.5 is 0.5
[65:12] times 0.5 is 0.5 so therefore we know that
[65:14] so therefore we know that this node here which we called this
[65:18] this node here which we called this its grad is just 0.5
[65:21] its grad is just 0.5 and we know that b dot grad is also 0.5
[65:24] and we know that b dot grad is also 0.5 so let's set those and let's draw
[65:28] so 0.5 continuing we have another plus
[65:32] continuing we have another plus 0.5 again we'll just distribute it so
[65:34] 0.5 again we'll just distribute it so 0.5 will flow to both of these
[65:37] 0.5 will flow to both of these so we can set
[65:39] so we can set theirs
[65:43] x2w2 as well that grad is 0.5
[65:47] x2w2 as well that grad is 0.5 and let's redraw pluses are my favorite
[65:50] and let's redraw pluses are my favorite uh operations to back propagate through
[65:51] uh operations to back propagate through because
[65:53] because it's very simple
[65:55] it's very simple so now it's flowing into these
[65:56] so now it's flowing into these expressions is 0.5 and so really again
[65:58] expressions is 0.5 and so really again keep in mind what the derivative is
[65:59] keep in mind what the derivative is telling us at every point in time along
[66:01] telling us at every point in time along here this is saying that
[66:04] here this is saying that if we want the output of this neuron to
[66:06] if we want the output of this neuron to increase
[66:08] increase then
[66:08] then the influence on these expressions is
[66:10] the influence on these expressions is positive on the output both of them are
[66:13] positive on the output both of them are positive
[66:16] contribution to the output
[66:20] so now back propagating to x2 and w2
[66:23] so now back propagating to x2 and w2 first
[66:24] first this is a times node so we know that the
[66:26] this is a times node so we know that the local derivative is you know the other
[66:28] local derivative is you know the other term
[66:28] term so if we want to calculate x2.grad
[66:32] so if we want to calculate x2.grad then
[66:33] then can you think through what it's going to
[66:34] can you think through what it's going to be
[66:40] so x2.grad will be w2.data
[66:44] w2.data times this x2w2
[66:48] times this x2w2 by grad right
[66:51] by grad right and
[66:52] and w2.grad will be
[66:55] w2.grad will be x2 that data times x2w2.grad
[67:01] right so that's the local piece of chain rule
[67:07] let's set them and let's redraw so here we see that the gradient on our
[67:11] so here we see that the gradient on our weight 2 is 0 because x2 data was 0
[67:15] weight 2 is 0 because x2 data was 0 right but x2 will have the gradient 0.5
[67:18] right but x2 will have the gradient 0.5 because data here was 1.
[67:20] because data here was 1. and so what's interesting here right is
[67:22] and so what's interesting here right is because the input x2 was 0 then because
[67:25] because the input x2 was 0 then because of the way the times works
[67:28] of the way the times works of course this gradient will be zero and
[67:30] of course this gradient will be zero and think about intuitively why that is
[67:33] think about intuitively why that is derivative always tells us the influence
[67:35] derivative always tells us the influence of
[67:36] of this on the final output if i wiggle w2
[67:39] this on the final output if i wiggle w2 how is the output changing
[67:41] how is the output changing it's not changing because we're
[67:42] it's not changing because we're multiplying by zero
[67:44] multiplying by zero so because it's not changing there's no
[67:46] so because it's not changing there's no derivative and zero is the correct
[67:47] derivative and zero is the correct answer
[67:48] answer because we're
[67:49] because we're squashing it at zero
[67:52] squashing it at zero and let's do it here point five should
[67:54] and let's do it here point five should come here and flow through this times
[67:57] come here and flow through this times and so we'll have that x1.grad is
[68:01] and so we'll have that x1.grad is can you think through a little bit what
[68:03] can you think through a little bit what what
[68:04] what this should be
[68:07] the local derivative of times with respect to x1 is going to be w1
[68:12] with respect to x1 is going to be w1 so w1 is data times
[68:15] so w1 is data times x1 w1 dot grad
[68:18] x1 w1 dot grad and w1.grad will be x1.data times
[68:23] and w1.grad will be x1.data times x1 w2 w1 with graph
[68:27] x1 w2 w1 with graph let's see what those came out to be
[68:29] let's see what those came out to be so this is 0.5 so this would be negative
[68:31] so this is 0.5 so this would be negative 1.5 and this would be 1.
[68:34] 1.5 and this would be 1. and we've back propagated through this
[68:36] and we've back propagated through this expression these are the actual final
[68:38] expression these are the actual final derivatives so if we want this neuron's
[68:40] derivatives so if we want this neuron's output to increase
[68:43] output to increase we know that what's necessary is that
[68:47] we know that what's necessary is that w2 we have no gradient w2 doesn't
[68:49] w2 we have no gradient w2 doesn't actually matter to this neuron right now
[68:51] actually matter to this neuron right now but this neuron this weight should uh go
[68:54] but this neuron this weight should uh go up
[68:55] up so if this weight goes up then this
[68:57] so if this weight goes up then this neuron's output would have gone up and
[68:59] neuron's output would have gone up and proportionally because the gradient is
[69:01] proportionally because the gradient is one okay so doing the back propagation
[69:03] one okay so doing the back propagation manually is obviously ridiculous so we
[69:05] manually is obviously ridiculous so we are now going to put an end to this
[69:06] are now going to put an end to this suffering and we're going to see how we
[69:08] suffering and we're going to see how we can implement uh the backward pass a bit
[69:11] can implement uh the backward pass a bit more automatically we're not going to be
[69:12] more automatically we're not going to be doing all of it manually out here
[69:14] doing all of it manually out here it's now pretty obvious to us by example
[69:17] it's now pretty obvious to us by example how these pluses and times are back
[69:18] how these pluses and times are back property ingredients so let's go up to
[69:20] property ingredients so let's go up to the value
[69:22] the value object and we're going to start
[69:24] object and we're going to start codifying what we've seen
[69:27] codifying what we've seen in the examples below
[69:29] in the examples below so we're going to do this by storing a
[69:31] so we're going to do this by storing a special cell dot backward
[69:34] special cell dot backward and underscore backward and this will be
[69:37] and underscore backward and this will be a function which is going to do that
[69:39] a function which is going to do that little piece of chain rule at each
[69:41] little piece of chain rule at each little node that compute that took
[69:43] little node that compute that took inputs and produced output uh we're
[69:45] inputs and produced output uh we're going to store
[69:46] going to store how we are going to chain the the
[69:49] how we are going to chain the the outputs gradient into the inputs
[69:51] outputs gradient into the inputs gradients
[69:52] gradients so by default
[69:54] so by default this will be a function
[69:55] this will be a function that uh doesn't do anything
[69:58] that uh doesn't do anything so um
[69:59] so um and you can also see that here in the
[70:01] and you can also see that here in the value in micrograb
[70:03] value in micrograb so
[70:04] so with this backward function by default
[70:06] with this backward function by default doesn't do anything
[70:08] doesn't do anything this is an empty function
[70:10] this is an empty function and that would be sort of the case for
[70:11] and that would be sort of the case for example for a leaf node for leaf node
[70:13] example for a leaf node for leaf node there's nothing to do
[70:15] there's nothing to do but now if when we're creating these out
[70:18] but now if when we're creating these out values these out values are an addition
[70:21] values these out values are an addition of self and other
[70:24] of self and other and so we will want to sell set
[70:27] and so we will want to sell set outs backward to be
[70:29] outs backward to be the function that propagates the
[70:31] the function that propagates the gradient
[70:34] so let's define what should happen
[70:40] and we're going to store it in a closure let's define what should happen when we
[70:44] let's define what should happen when we call
[70:45] call outs grad
[70:47] for in addition
[70:50] for in addition our job is to take
[70:52] our job is to take outs grad and propagate it into self's
[70:55] outs grad and propagate it into self's grad and other grad so basically we want
[70:57] grad and other grad so basically we want to sell self.grad to something
[71:00] to sell self.grad to something and we want to set others.grad to
[71:02] and we want to set others.grad to something
[71:04] something okay
[71:05] okay and the way we saw below how chain rule
[71:08] and the way we saw below how chain rule works we want to take the local
[71:10] works we want to take the local derivative times
[71:11] derivative times the
[71:12] the sort of global derivative i should call
[71:14] sort of global derivative i should call it which is the derivative of the final
[71:16] it which is the derivative of the final output of the expression with respect to
[71:18] output of the expression with respect to out's data
[71:21] out's data with respect to out
[71:22] with respect to out so
[71:24] so the local derivative of self in an
[71:27] the local derivative of self in an addition is 1.0
[71:29] addition is 1.0 so it's just 1.0 times
[71:31] so it's just 1.0 times outs grad
[71:34] outs grad that's the chain rule
[71:35] that's the chain rule and others.grad will be 1.0 times
[71:38] and others.grad will be 1.0 times outgrad
[71:39] outgrad and what you basically what you're
[71:40] and what you basically what you're seeing here is that outscrad
[71:42] seeing here is that outscrad will simply be copied onto selfs grad
[71:45] will simply be copied onto selfs grad and others grad as we saw happens for an
[71:48] and others grad as we saw happens for an addition operation
[71:49] addition operation so we're going to later call this
[71:51] so we're going to later call this function to propagate the gradient
[71:53] function to propagate the gradient having done an addition
[71:55] having done an addition let's now do multiplication we're going
[71:57] let's now do multiplication we're going to also define that backward
[72:02] and we're going to set its backward to be backward
[72:07] and we want to chain outgrad into
[72:11] and we want to chain outgrad into self.grad
[72:14] and others.grad
[72:17] and others.grad and this will be a little piece of chain
[72:18] and this will be a little piece of chain rule for multiplication
[72:20] rule for multiplication so we'll have
[72:21] so we'll have so what should this be
[72:23] so what should this be can you think through
[72:28] so what is the local derivative here the local derivative was
[72:32] here the local derivative was others.data
[72:35] and then oops others.data and the times of that
[72:39] oops others.data and the times of that grad that's channel
[72:42] grad that's channel and here we have self.data times of that
[72:44] and here we have self.data times of that grad
[72:45] grad that's what we've been doing
[72:49] and finally here for 10 h left backward
[72:54] and then we want to set out backwards to
[72:57] and then we want to set out backwards to be just backward
[73:00] and here we need to back propagate we have out that grad and
[73:04] back propagate we have out that grad and we want to chain it into self.grad
[73:09] and salt.grad will be the local derivative of this operation
[73:13] the local derivative of this operation that we've done here which is 10h
[73:16] that we've done here which is 10h and so we saw that the local the
[73:17] and so we saw that the local the gradient is 1 minus the tan h of x
[73:20] gradient is 1 minus the tan h of x squared which here is t
[73:23] squared which here is t that's the local derivative because
[73:25] that's the local derivative because that's t is the output of this 10 h so 1
[73:27] that's t is the output of this 10 h so 1 minus t squared is the local derivative
[73:30] minus t squared is the local derivative and then gradient um
[73:32] and then gradient um has to be multiplied because of the
[73:33] has to be multiplied because of the chain rule
[73:34] chain rule so outgrad is chained through the local
[73:36] so outgrad is chained through the local gradient into salt.grad
[73:39] gradient into salt.grad and that should be basically it so we're
[73:41] and that should be basically it so we're going to redefine our value node
[73:44] going to redefine our value node we're going to swing all the way down
[73:46] we're going to swing all the way down here
[73:48] here and we're going to
[73:49] and we're going to redefine
[73:51] redefine our expression
[73:52] our expression make sure that all the grads are zero
[73:55] make sure that all the grads are zero okay
[73:56] okay but now we don't have to do this
[73:57] but now we don't have to do this manually anymore
[73:59] manually anymore we are going to basically be calling the
[74:01] we are going to basically be calling the dot backward in the right order
[74:04] dot backward in the right order so
[74:05] so first we want to call os
[74:07] first we want to call os dot backwards
[74:14] so o was the outcome of 10h
[74:17] so o was the outcome of 10h right so calling all that those who's
[74:20] right so calling all that those who's backward
[74:22] backward will be
[74:23] will be this function this is what it will do
[74:26] this function this is what it will do now we have to be careful because
[74:29] now we have to be careful because there's a times out.grad
[74:31] there's a times out.grad and out.grad remember is initialized to
[74:34] and out.grad remember is initialized to zero
[74:38] so here we see grad zero so as a base
[74:41] so here we see grad zero so as a base case we need to set both.grad to 1.0
[74:46] case we need to set both.grad to 1.0 to initialize this with 1
[74:53] and then once this is 1 we can call oda
[74:56] and then once this is 1 we can call oda backward
[74:57] backward and what that should do is it should
[74:58] and what that should do is it should propagate this grad through 10h
[75:02] propagate this grad through 10h so the local derivative times
[75:04] so the local derivative times the global derivative which is
[75:05] the global derivative which is initialized at one so
[75:08] initialized at one so this should
[75:11] this should um
[75:15] a dope so i thought about redoing it but i
[75:19] so i thought about redoing it but i figured i should just leave the error in
[75:20] figured i should just leave the error in here because it's pretty funny why is
[75:22] here because it's pretty funny why is anti-object not callable
[75:24] anti-object not callable uh it's because
[75:27] uh it's because i screwed up we're trying to save these
[75:29] i screwed up we're trying to save these functions so this is correct
[75:31] functions so this is correct this here
[75:33] this here we don't want to call the function
[75:34] we don't want to call the function because that returns none these
[75:36] because that returns none these functions return none we just want to
[75:38] functions return none we just want to store the function
[75:39] store the function so let me redefine the value object
[75:42] so let me redefine the value object and then we're going to come back in
[75:43] and then we're going to come back in redefine the expression draw a dot
[75:46] redefine the expression draw a dot everything is great o dot grad is one
[75:50] everything is great o dot grad is one o dot grad is one and now
[75:53] o dot grad is one and now now this should work of course
[75:55] now this should work of course okay so all that backward should
[75:58] okay so all that backward should this grant should now be 0.5 if we
[76:00] this grant should now be 0.5 if we redraw and if everything went correctly
[76:03] redraw and if everything went correctly 0.5 yay
[76:05] 0.5 yay okay so now we need to call ns.grad
[76:10] and it's not awkward sorry
[76:13] and it's not awkward sorry ends backward
[76:14] ends backward so that seems to have worked
[76:17] so instead backward routed the gradient
[76:21] so instead backward routed the gradient to both of these so this is looking
[76:22] to both of these so this is looking great
[76:24] great now we could of course called uh called
[76:26] now we could of course called uh called b grad
[76:27] b grad beat up backwards sorry
[76:30] beat up backwards sorry what's gonna happen
[76:32] what's gonna happen well b doesn't have it backward b is
[76:34] well b doesn't have it backward b is backward
[76:35] backward because b is a leaf node
[76:37] because b is a leaf node b's backward is by initialization the
[76:40] b's backward is by initialization the empty function
[76:41] empty function so nothing would happen but we can call
[76:44] so nothing would happen but we can call call it on it
[76:45] call it on it but when we call
[76:48] but when we call this one
[76:50] this one it's backward
[76:53] then we expect this 0.5 to get further
[76:56] then we expect this 0.5 to get further routed
[76:57] routed right so there we go 0.5.5
[77:00] right so there we go 0.5.5 and then finally
[77:02] and then finally we want to call
[77:05] we want to call it here on x2 w2
[77:10] and on x1 w1
[77:16] do both of those and there we go
[77:19] and there we go so we get 0 0.5 negative 1.5 and 1
[77:23] so we get 0 0.5 negative 1.5 and 1 exactly as we did before but now
[77:26] exactly as we did before but now we've done it through
[77:28] we've done it through calling that backward um
[77:30] calling that backward um sort of manually
[77:32] sort of manually so we have the lamp one last piece to
[77:34] so we have the lamp one last piece to get rid of which is us calling
[77:36] get rid of which is us calling underscore backward manually so let's
[77:38] underscore backward manually so let's think through what we are actually doing
[77:40] think through what we are actually doing um
[77:41] um we've laid out a mathematical expression
[77:43] we've laid out a mathematical expression and now we're trying to go backwards
[77:44] and now we're trying to go backwards through that expression
[77:46] through that expression um so going backwards through the
[77:48] um so going backwards through the expression just means that we never want
[77:50] expression just means that we never want to call a dot backward for any node
[77:54] to call a dot backward for any node before
[77:55] before we've done a sort of um everything after
[77:58] we've done a sort of um everything after it
[77:59] it so we have to do everything after it
[78:01] so we have to do everything after it before we're ever going to call that
[78:02] before we're ever going to call that backward on any one node we have to get
[78:04] backward on any one node we have to get all of its full dependencies everything
[78:06] all of its full dependencies everything that it depends on has to
[78:08] that it depends on has to propagate to it before we can continue
[78:10] propagate to it before we can continue back propagation so this ordering of
[78:14] back propagation so this ordering of graphs can be achieved using something
[78:16] graphs can be achieved using something called topological sort
[78:17] called topological sort so topological sort
[78:20] so topological sort is basically a laying out of a graph
[78:23] is basically a laying out of a graph such that all the edges go only from
[78:24] such that all the edges go only from left to right basically
[78:26] left to right basically so here we have a graph it's a directory
[78:29] so here we have a graph it's a directory a cyclic graph a dag
[78:31] a cyclic graph a dag and this is two different topological
[78:34] and this is two different topological orders of it i believe where basically
[78:36] orders of it i believe where basically you'll see that it's laying out of the
[78:37] you'll see that it's laying out of the notes such that all the edges go only
[78:39] notes such that all the edges go only one way from left to right
[78:41] one way from left to right and implementing topological sort you
[78:44] and implementing topological sort you can look in wikipedia and so on i'm not
[78:46] can look in wikipedia and so on i'm not going to go through it in detail
[78:48] going to go through it in detail but basically this is what builds a
[78:51] but basically this is what builds a topological graph
[78:54] topological graph we maintain a set of visited nodes and
[78:56] we maintain a set of visited nodes and then we are
[78:59] then we are going through starting at some root node
[79:02] going through starting at some root node which for us is o that's where we want
[79:03] which for us is o that's where we want to start the topological sort
[79:05] to start the topological sort and starting at o we go through all of
[79:08] and starting at o we go through all of its children and we need to lay them out
[79:10] its children and we need to lay them out from left to right
[79:12] from left to right and basically this starts at o
[79:14] and basically this starts at o if it's not visited then it marks it as
[79:17] if it's not visited then it marks it as visited and then it iterates through all
[79:19] visited and then it iterates through all of its children
[79:20] of its children and calls build topological on them
[79:24] and calls build topological on them and then uh after it's gone through all
[79:26] and then uh after it's gone through all the children it adds itself
[79:28] the children it adds itself so basically
[79:29] so basically this node that we're going to call it on
[79:31] this node that we're going to call it on like say o is only going to add itself
[79:34] like say o is only going to add itself to the topo list after all of the
[79:37] to the topo list after all of the children have been processed and that's
[79:39] children have been processed and that's how this function is guaranteeing
[79:41] how this function is guaranteeing that you're only going to be in the list
[79:43] that you're only going to be in the list once all your children are in the list
[79:45] once all your children are in the list and that's the invariant that is being
[79:46] and that's the invariant that is being maintained so if we built upon o and
[79:49] maintained so if we built upon o and then inspect this list
[79:52] then inspect this list we're going to see that it ordered our
[79:54] we're going to see that it ordered our value objects
[79:56] value objects and the last one
[79:58] and the last one is the value of 0.707 which is the
[80:00] is the value of 0.707 which is the output
[80:01] output so this is o and then this is n
[80:04] so this is o and then this is n and then all the other nodes get laid
[80:07] and then all the other nodes get laid out before it
[80:09] out before it so that builds the topological graph and
[80:12] so that builds the topological graph and really what we're doing now is we're
[80:13] really what we're doing now is we're just calling dot underscore backward on
[80:16] just calling dot underscore backward on all of the nodes in a topological order
[80:19] all of the nodes in a topological order so if we just reset the gradients
[80:22] so if we just reset the gradients they're all zero
[80:23] they're all zero what did we do
[80:24] what did we do we started by
[80:27] we started by setting o dot grad
[80:29] setting o dot grad to b1
[80:31] to b1 that's the base case
[80:33] that's the base case then we built the topological order
[80:38] and then we went for node
[80:41] and then we went for node in
[80:42] in reversed
[80:44] reversed of topo
[80:46] of topo now
[80:47] now in in the reverse order because this
[80:49] in in the reverse order because this list goes from
[80:50] list goes from you know we need to go through it in
[80:52] you know we need to go through it in reversed order
[80:53] reversed order so starting at o
[80:56] so starting at o note that backward
[80:58] note that backward and this should be
[81:01] and this should be it
[81:03] it there we go
[81:05] there we go those are the correct derivatives
[81:07] those are the correct derivatives finally we are going to hide this
[81:08] finally we are going to hide this functionality
[81:10] functionality so i'm going to
[81:11] so i'm going to copy this and we're going to hide it
[81:13] copy this and we're going to hide it inside the valley class because we don't
[81:15] inside the valley class because we don't want to have all that code lying around
[81:18] want to have all that code lying around so instead of an underscore backward
[81:19] so instead of an underscore backward we're now going to define an actual
[81:21] we're now going to define an actual backward so that's backward without the
[81:23] backward so that's backward without the underscore
[81:26] underscore and that's going to do all the stuff
[81:27] and that's going to do all the stuff that we just arrived
[81:29] that we just arrived so let me just clean this up a little
[81:30] so let me just clean this up a little bit so
[81:32] bit so we're first going to
[81:37] build a topological graph starting at self
[81:41] starting at self so build topo of self
[81:44] so build topo of self will populate the topological order into
[81:46] will populate the topological order into the topo list which is a local variable
[81:49] the topo list which is a local variable then we set self.grad to be one
[81:52] then we set self.grad to be one and then for each node in the reversed
[81:55] and then for each node in the reversed list so starting at us and going to all
[81:57] list so starting at us and going to all the children
[82:00] the children underscore backward
[82:02] underscore backward and
[82:03] and that should be it so
[82:06] that should be it so save
[82:08] save come down here
[82:09] come down here redefine
[82:09] redefine [Music]
[82:11] [Music] okay all the grands are zero
[82:13] okay all the grands are zero and now what we can do is oh that
[82:15] and now what we can do is oh that backward without the underscore
[82:17] backward without the underscore and
[82:21] there we go and that's uh that's back propagation
[82:26] and that's uh that's back propagation place for one neuron
[82:28] place for one neuron now we shouldn't be too happy with
[82:29] now we shouldn't be too happy with ourselves actually because we have a bad
[82:32] ourselves actually because we have a bad bug um and we have not surfaced the bug
[82:35] bug um and we have not surfaced the bug because of some specific conditions that
[82:36] because of some specific conditions that we are we have to think about right now
[82:39] we are we have to think about right now so here's the simplest case that shows
[82:42] so here's the simplest case that shows the bug
[82:43] the bug say i create a single node a
[82:48] and then i create a b that is a plus a
[82:51] and then i create a b that is a plus a and then i called backward
[82:54] so what's going to happen is a is 3
[82:57] so what's going to happen is a is 3 and then a b is a plus a so there's two
[83:00] and then a b is a plus a so there's two arrows on top of each other here
[83:03] then we can see that b is of course the forward pass works
[83:06] forward pass works b is just
[83:08] b is just a plus a which is six
[83:10] a plus a which is six but the gradient here is not actually
[83:11] but the gradient here is not actually correct
[83:12] correct that we calculate it automatically
[83:15] that we calculate it automatically and that's because
[83:17] and that's because um
[83:19] um of course uh
[83:20] of course uh just doing calculus in your head the
[83:22] just doing calculus in your head the derivative of b with respect to a
[83:24] derivative of b with respect to a should be uh two
[83:27] should be uh two one plus one
[83:28] one plus one it's not one
[83:30] it's not one intuitively what's happening here right
[83:32] intuitively what's happening here right so b is the result of a plus a and then
[83:34] so b is the result of a plus a and then we call backward on it
[83:36] we call backward on it so let's go up and see what that does
[83:42] um b is a result of addition
[83:45] b is a result of addition so out as
[83:46] so out as b and then when we called backward what
[83:49] b and then when we called backward what happened is
[83:50] happened is self.grad was set
[83:53] self.grad was set to one
[83:54] to one and then other that grad was set to one
[83:57] and then other that grad was set to one but because we're doing a plus a
[83:59] but because we're doing a plus a self and other are actually the exact
[84:02] self and other are actually the exact same object
[84:03] same object so we are overriding the gradient we are
[84:06] so we are overriding the gradient we are setting it to one and then we are
[84:07] setting it to one and then we are setting it again to one and that's why
[84:10] setting it again to one and that's why it stays
[84:11] it stays at one
[84:13] at one so that's a problem
[84:14] so that's a problem there's another way to see this in a
[84:16] there's another way to see this in a little bit more complicated expression
[84:21] so here we have a and b
[84:25] a and b and then uh d will be the multiplication
[84:28] and then uh d will be the multiplication of the two and e will be the addition of
[84:30] of the two and e will be the addition of the two
[84:33] and then we multiply e times d to get f and
[84:35] then we multiply e times d to get f and then we called fda backward
[84:37] then we called fda backward and these gradients if you check will be
[84:39] and these gradients if you check will be incorrect
[84:40] incorrect so fundamentally what's happening here
[84:42] so fundamentally what's happening here again is
[84:45] again is basically we're going to see an issue
[84:46] basically we're going to see an issue anytime we use a variable more than once
[84:49] anytime we use a variable more than once until now in these expressions above
[84:51] until now in these expressions above every variable is used exactly once so
[84:53] every variable is used exactly once so we didn't see the issue
[84:54] we didn't see the issue but here if a variable is used more than
[84:56] but here if a variable is used more than once what's going to happen during
[84:57] once what's going to happen during backward pass we're backpropagating from
[85:00] backward pass we're backpropagating from f to e to d so far so good but now
[85:03] f to e to d so far so good but now equals it backward and it deposits its
[85:05] equals it backward and it deposits its gradients to a and b but then we come
[85:08] gradients to a and b but then we come back to d
[85:09] back to d and call backward and it overwrites
[85:11] and call backward and it overwrites those gradients at a and b
[85:14] those gradients at a and b so that's obviously a problem
[85:17] so that's obviously a problem and the solution here if you look at
[85:19] and the solution here if you look at the multivariate case of the chain rule
[85:22] the multivariate case of the chain rule and its generalization there
[85:23] and its generalization there the solution there is basically that we
[85:26] the solution there is basically that we have to accumulate these gradients these
[85:28] have to accumulate these gradients these gradients add
[85:30] gradients add and so instead of setting those
[85:32] and so instead of setting those gradients
[85:34] gradients we can simply do plus equals we need to
[85:37] we can simply do plus equals we need to accumulate those gradients
[85:39] accumulate those gradients plus equals plus equals
[85:41] plus equals plus equals plus equals
[85:44] plus equals and this will be okay remember because
[85:48] and this will be okay remember because we are initializing them at zero so they
[85:50] we are initializing them at zero so they start at zero
[85:51] start at zero and then any
[85:53] and then any contribution
[85:54] contribution that flows backwards
[85:57] that flows backwards will simply add
[85:58] will simply add so now if we redefine
[86:01] so now if we redefine this one
[86:03] this one because the plus equals this now works
[86:06] because the plus equals this now works because a.grad started at zero and we
[86:08] because a.grad started at zero and we called beta backward we deposit one and
[86:11] called beta backward we deposit one and then we deposit one again and now this
[86:13] then we deposit one again and now this is two which is correct
[86:14] is two which is correct and here this will also work and we'll
[86:16] and here this will also work and we'll get correct gradients
[86:18] get correct gradients because when we call eta backward we
[86:20] because when we call eta backward we will deposit the gradients from this
[86:21] will deposit the gradients from this branch and then we get to back into
[86:23] branch and then we get to back into detail backward it will deposit its own
[86:26] detail backward it will deposit its own gradients and then those gradients
[86:28] gradients and then those gradients simply add on top of each other and so
[86:30] simply add on top of each other and so we just accumulate those gradients and
[86:31] we just accumulate those gradients and that fixes the issue okay now before we
[86:34] that fixes the issue okay now before we move on let me actually do a bit of
[86:35] move on let me actually do a bit of cleanup here and delete some of these
[86:38] cleanup here and delete some of these some of this intermediate work so
[86:41] some of this intermediate work so we're not gonna need any of this now
[86:42] we're not gonna need any of this now that we've derived all of it
[86:44] that we've derived all of it um
[86:45] um we are going to keep this because i want
[86:48] we are going to keep this because i want to come back to it
[86:49] to come back to it delete the 10h
[86:51] delete the 10h delete our morning example
[86:53] delete our morning example delete the step
[86:55] delete the step delete this keep the code that draws
[86:59] delete this keep the code that draws and then delete this example
[87:02] and then delete this example and leave behind only the definition of
[87:03] and leave behind only the definition of value
[87:05] value and now let's come back to this
[87:06] and now let's come back to this non-linearity here that we implemented
[87:08] non-linearity here that we implemented the tanh now i told you that we could
[87:10] the tanh now i told you that we could have broken down 10h into its explicit
[87:13] have broken down 10h into its explicit atoms in terms of other expressions if
[87:16] atoms in terms of other expressions if we had the x function so if you remember
[87:18] we had the x function so if you remember tan h is defined like this and we chose
[87:20] tan h is defined like this and we chose to develop tan h as a single function
[87:22] to develop tan h as a single function and we can do that because we know its
[87:24] and we can do that because we know its derivative and we can back propagate
[87:26] derivative and we can back propagate through it
[87:26] through it but we can also break down tan h into
[87:29] but we can also break down tan h into and express it as a function of x and i
[87:31] and express it as a function of x and i would like to do that now because i want
[87:33] would like to do that now because i want to prove to you that you get all the
[87:34] to prove to you that you get all the same results and all those ingredients
[87:36] same results and all those ingredients but also because it forces us to
[87:38] but also because it forces us to implement a few more expressions it
[87:40] implement a few more expressions it forces us to do exponentiation addition
[87:42] forces us to do exponentiation addition subtraction division and things like
[87:44] subtraction division and things like that and i think it's a good exercise to
[87:46] that and i think it's a good exercise to go through a few more of these
[87:48] go through a few more of these okay so let's scroll up
[87:50] okay so let's scroll up to the definition of value
[87:52] to the definition of value and here one thing that we currently
[87:53] and here one thing that we currently can't do is we can do like a value of
[87:56] can't do is we can do like a value of say 2.0
[87:58] say 2.0 but we can't do you know here for
[88:00] but we can't do you know here for example we want to add constant one and
[88:02] example we want to add constant one and we can't do something like this
[88:05] we can't do something like this and we can't do it because it says
[88:06] and we can't do it because it says object has no attribute data that's
[88:08] object has no attribute data that's because a plus one comes right here to
[88:11] because a plus one comes right here to add
[88:12] add and then other is the integer one and
[88:14] and then other is the integer one and then here python is trying to access
[88:16] then here python is trying to access one.data and that's not a thing and
[88:18] one.data and that's not a thing and that's because basically one is not a
[88:20] that's because basically one is not a value object and we only have addition
[88:22] value object and we only have addition for value objects so as a matter of
[88:24] for value objects so as a matter of convenience so that we can create
[88:26] convenience so that we can create expressions like this and make them make
[88:28] expressions like this and make them make sense
[88:29] sense we can simply do something like this
[88:32] we can simply do something like this basically
[88:33] basically we let other alone if other is an
[88:35] we let other alone if other is an instance of value but if it's not an
[88:37] instance of value but if it's not an instance of value we're going to assume
[88:39] instance of value we're going to assume that it's a number like an integer float
[88:40] that it's a number like an integer float and we're going to simply wrap it in in
[88:43] and we're going to simply wrap it in in value and then other will just become
[88:45] value and then other will just become value of other and then other will have
[88:46] value of other and then other will have a data attribute and this should work so
[88:49] a data attribute and this should work so if i just say this predefined value then
[88:51] if i just say this predefined value then this should work
[88:53] this should work there we go okay now let's do the exact
[88:55] there we go okay now let's do the exact same thing for multiply because we can't
[88:57] same thing for multiply because we can't do something like this
[88:58] do something like this again
[88:59] again for the exact same reason so we just
[89:01] for the exact same reason so we just have to go to mole and if other is
[89:04] have to go to mole and if other is not a value then let's wrap it in value
[89:07] not a value then let's wrap it in value let's redefine value and now this works
[89:10] let's redefine value and now this works now here's a kind of unfortunate and not
[89:12] now here's a kind of unfortunate and not obvious part a times two works we saw
[89:15] obvious part a times two works we saw that but two times a is that gonna work
[89:19] that but two times a is that gonna work you'd expect it to right but actually it
[89:21] you'd expect it to right but actually it will not
[89:22] will not and the reason it won't is because
[89:24] and the reason it won't is because python doesn't know
[89:26] python doesn't know like when when you do a times two
[89:28] like when when you do a times two basically um so a times two python will
[89:31] basically um so a times two python will go and it will basically do something
[89:32] go and it will basically do something like a dot mul
[89:34] like a dot mul of two that's basically what it will
[89:36] of two that's basically what it will call but to it 2 times a is the same as
[89:39] call but to it 2 times a is the same as 2 dot mol of a
[89:41] 2 dot mol of a and it doesn't 2 can't multiply
[89:44] and it doesn't 2 can't multiply value and so it's really confused about
[89:46] value and so it's really confused about that
[89:47] that so instead what happens is in python the
[89:49] so instead what happens is in python the way this works is you are free to define
[89:51] way this works is you are free to define something called the r mold
[89:54] something called the r mold and our mole
[89:55] and our mole is kind of like a fallback so if python
[89:58] is kind of like a fallback so if python can't do 2 times a it will check if um
[90:02] can't do 2 times a it will check if um if by any chance a knows how to multiply
[90:05] if by any chance a knows how to multiply two and that will be called into our
[90:07] two and that will be called into our mole
[90:08] mole so because python can't do two times a
[90:11] so because python can't do two times a it will check is there an our mole in
[90:12] it will check is there an our mole in value and because there is it will now
[90:15] value and because there is it will now call that
[90:16] call that and what we'll do here is we will swap
[90:18] and what we'll do here is we will swap the order of the operands so basically
[90:21] the order of the operands so basically two times a will redirect to armel and
[90:23] two times a will redirect to armel and our mole will basically call a times two
[90:26] our mole will basically call a times two and that's how that will work
[90:28] and that's how that will work so
[90:29] so redefining now with armor two times a
[90:31] redefining now with armor two times a becomes four okay now looking at the
[90:33] becomes four okay now looking at the other elements that we still need we
[90:34] other elements that we still need we need to know how to exponentiate and how
[90:36] need to know how to exponentiate and how to divide so let's first the explanation
[90:38] to divide so let's first the explanation to the exponentiation part we're going
[90:40] to the exponentiation part we're going to introduce
[90:41] to introduce a single
[90:42] a single function x here
[90:45] function x here and x is going to mirror 10h in the
[90:47] and x is going to mirror 10h in the sense that it's a simple single function
[90:49] sense that it's a simple single function that transforms a single scalar value
[90:51] that transforms a single scalar value and outputs a single scalar value
[90:53] and outputs a single scalar value so we pop out the python number we use
[90:56] so we pop out the python number we use math.x to exponentiate it create a new
[90:58] math.x to exponentiate it create a new value object
[90:59] value object everything that we've seen before the
[91:00] everything that we've seen before the tricky part of course is how do you
[91:02] tricky part of course is how do you propagate through e to the x
[91:04] propagate through e to the x and
[91:05] and so here you can potentially pause the
[91:07] so here you can potentially pause the video and think about what should go
[91:09] video and think about what should go here
[91:13] okay so basically we need to know what is the local derivative of e to the x so
[91:18] is the local derivative of e to the x so d by d x of e to the x is famously just
[91:21] d by d x of e to the x is famously just e to the x and we've already just
[91:23] e to the x and we've already just calculated e to the x and it's inside
[91:25] calculated e to the x and it's inside out that data so we can do up that data
[91:27] out that data so we can do up that data times
[91:28] times and
[91:29] and out that grad that's the chain rule
[91:32] out that grad that's the chain rule so we're just chaining on to the current
[91:33] so we're just chaining on to the current running grad
[91:35] running grad and this is what the expression looks
[91:36] and this is what the expression looks like it looks a little confusing but
[91:38] like it looks a little confusing but this is what it is and that's the
[91:40] this is what it is and that's the exponentiation
[91:41] exponentiation so redefining we should now be able to
[91:43] so redefining we should now be able to call a.x
[91:45] call a.x and
[91:46] and hopefully the backward pass works as
[91:47] hopefully the backward pass works as well okay and the last thing we'd like
[91:49] well okay and the last thing we'd like to do of course is we'd like to be able
[91:50] to do of course is we'd like to be able to divide
[91:52] to divide now
[91:53] now i actually will implement something
[91:54] i actually will implement something slightly more powerful than division
[91:56] slightly more powerful than division because division is just a special case
[91:57] because division is just a special case of something a bit more powerful
[91:59] of something a bit more powerful so in particular just by rearranging
[92:02] so in particular just by rearranging if we have some kind of a b equals
[92:04] if we have some kind of a b equals value of 4.0 here we'd like to basically
[92:07] value of 4.0 here we'd like to basically be able to do a divide b and we'd like
[92:09] be able to do a divide b and we'd like this to be able to give us 0.5
[92:11] this to be able to give us 0.5 now division actually can be reshuffled
[92:14] now division actually can be reshuffled as follows if we have a divide b that's
[92:17] as follows if we have a divide b that's actually the same as a multiplying one
[92:18] actually the same as a multiplying one over b
[92:19] over b and that's the same as a multiplying b
[92:21] and that's the same as a multiplying b to the power of negative one
[92:24] to the power of negative one and so what i'd like to do instead is i
[92:25] and so what i'd like to do instead is i basically like to implement the
[92:27] basically like to implement the operation of x to the k for some
[92:29] operation of x to the k for some constant uh k so it's an integer or a
[92:32] constant uh k so it's an integer or a float um and we would like to be able to
[92:35] float um and we would like to be able to differentiate this and then as a special
[92:36] differentiate this and then as a special case uh negative one will be division
[92:40] case uh negative one will be division and so i'm doing that just because uh
[92:42] and so i'm doing that just because uh it's more general and um yeah you might
[92:45] it's more general and um yeah you might as well do it that way so basically what
[92:46] as well do it that way so basically what i'm saying is we can redefine
[92:49] i'm saying is we can redefine uh division
[92:51] uh division which we will put here somewhere
[92:54] which we will put here somewhere yeah we can put it here somewhere what
[92:56] yeah we can put it here somewhere what i'm saying is that we can redefine
[92:58] i'm saying is that we can redefine division so self-divide other
[93:00] division so self-divide other can actually be rewritten as self times
[93:03] can actually be rewritten as self times other to the power of negative one
[93:05] other to the power of negative one and now
[93:07] and now a value raised to the power of negative
[93:09] a value raised to the power of negative one we have now defined that
[93:11] one we have now defined that so
[93:12] so here's
[93:13] here's so we need to implement the pow function
[93:15] so we need to implement the pow function where am i going to put the power
[93:17] where am i going to put the power function maybe here somewhere
[93:20] function maybe here somewhere this is the skeleton for it
[93:22] this is the skeleton for it so this function will be called when we
[93:24] so this function will be called when we try to raise a value to some power and
[93:26] try to raise a value to some power and other will be that power
[93:28] other will be that power now i'd like to make sure that other is
[93:30] now i'd like to make sure that other is only an int or a float usually other is
[93:33] only an int or a float usually other is some kind of a different value object
[93:35] some kind of a different value object but here other will be forced to be an
[93:37] but here other will be forced to be an end or a float otherwise the math
[93:40] end or a float otherwise the math won't work for
[93:42] won't work for for or try to achieve in the specific
[93:43] for or try to achieve in the specific case that would be a different
[93:45] case that would be a different derivative expression if we wanted other
[93:47] derivative expression if we wanted other to be a value
[93:49] to be a value so here we create the output value which
[93:51] so here we create the output value which is just uh you know this data raised to
[93:53] is just uh you know this data raised to the power of other and other here could
[93:55] the power of other and other here could be for example negative one that's what
[93:56] be for example negative one that's what we are hoping to achieve
[93:59] we are hoping to achieve and then uh this is the backwards stub
[94:01] and then uh this is the backwards stub and this is the fun part which is what
[94:03] and this is the fun part which is what is the uh chain rule expression here for
[94:07] is the uh chain rule expression here for back for um
[94:09] back for um back propagating through the power
[94:11] back propagating through the power function where the power is to the power
[94:13] function where the power is to the power of some kind of a constant
[94:15] of some kind of a constant so this is the exercise and maybe pause
[94:17] so this is the exercise and maybe pause the video here and see if you can figure
[94:18] the video here and see if you can figure it out yourself as to what we should put
[94:20] it out yourself as to what we should put here
[94:26] okay so
[94:29] okay so you can actually go here and look at
[94:30] you can actually go here and look at derivative rules as an example and we
[94:32] derivative rules as an example and we see lots of derivatives that you can
[94:34] see lots of derivatives that you can hopefully know from calculus in
[94:36] hopefully know from calculus in particular what we're looking for is the
[94:37] particular what we're looking for is the power rule
[94:39] power rule because that's telling us that if we're
[94:40] because that's telling us that if we're trying to take d by dx of x to the n
[94:42] trying to take d by dx of x to the n which is what we're doing here
[94:44] which is what we're doing here then that is just n times x to the n
[94:46] then that is just n times x to the n minus 1
[94:48] minus 1 right
[94:49] right okay
[94:50] okay so
[94:51] so that's telling us about the local
[94:53] that's telling us about the local derivative of this power operation
[94:55] derivative of this power operation so all we want here
[94:58] so all we want here basically n is now other
[95:00] basically n is now other and self.data is x
[95:03] and self.data is x and so this now becomes
[95:06] and so this now becomes other which is n times
[95:08] other which is n times self.data
[95:10] self.data which is now a python in torah float
[95:13] which is now a python in torah float it's not a valley object we're accessing
[95:14] it's not a valley object we're accessing the data attribute
[95:16] the data attribute raised
[95:17] raised to the power of other minus one or n
[95:19] to the power of other minus one or n minus one
[95:21] minus one i can put brackets around this but this
[95:22] i can put brackets around this but this doesn't matter because
[95:25] doesn't matter because power takes precedence over multiply and
[95:27] power takes precedence over multiply and python so that would have been okay
[95:29] python so that would have been okay and that's the local derivative only but
[95:31] and that's the local derivative only but now we have to chain it and we change
[95:33] now we have to chain it and we change just simply by multiplying by output
[95:34] just simply by multiplying by output grad that's chain rule
[95:36] grad that's chain rule and this should technically work
[95:40] and this should technically work and we're going to find out soon but now
[95:42] and we're going to find out soon but now if we
[95:43] if we do this this should now work
[95:46] do this this should now work and we get 0.5 so the forward pass works
[95:49] and we get 0.5 so the forward pass works but does the backward pass work and i
[95:51] but does the backward pass work and i realize that we actually also have to
[95:52] realize that we actually also have to know how to subtract so
[95:54] know how to subtract so right now a minus b will not work
[95:57] right now a minus b will not work to make it work we need one more
[96:00] to make it work we need one more piece of code here
[96:01] piece of code here and
[96:02] and basically this is the
[96:05] basically this is the subtraction and the way we're going to
[96:06] subtraction and the way we're going to implement subtraction is we're going to
[96:08] implement subtraction is we're going to implement it by addition of a negation
[96:10] implement it by addition of a negation and then to implement negation we're
[96:12] and then to implement negation we're gonna multiply by negative one so just
[96:14] gonna multiply by negative one so just again using the stuff we've already
[96:15] again using the stuff we've already built and just um expressing it in terms
[96:17] built and just um expressing it in terms of what we have and a minus b is now
[96:20] of what we have and a minus b is now working okay so now let's scroll again
[96:22] working okay so now let's scroll again to this expression here for this neuron
[96:25] to this expression here for this neuron and let's just
[96:26] and let's just compute the backward pass here once
[96:28] compute the backward pass here once we've defined o
[96:30] we've defined o and let's draw it
[96:32] and let's draw it so here's the gradients for all these
[96:33] so here's the gradients for all these leaf nodes for this two-dimensional
[96:35] leaf nodes for this two-dimensional neuron that has a 10h that we've seen
[96:37] neuron that has a 10h that we've seen before so now what i'd like to do is i'd
[96:39] before so now what i'd like to do is i'd like to break up this 10h
[96:41] like to break up this 10h into this expression here
[96:44] into this expression here so let me copy paste this
[96:46] so let me copy paste this here
[96:47] here and now instead of we'll preserve the
[96:49] and now instead of we'll preserve the label
[96:50] label and we will change how we define o
[96:53] and we will change how we define o so in particular we're going to
[96:55] so in particular we're going to implement this formula here
[96:56] implement this formula here so we need e to the 2x
[96:58] so we need e to the 2x minus 1 over e to the x plus 1. so e to
[97:01] minus 1 over e to the x plus 1. so e to the 2x we need to take 2 times n and we
[97:04] the 2x we need to take 2 times n and we need to exponentiate it that's e to the
[97:07] need to exponentiate it that's e to the two x and then because we're using it
[97:08] two x and then because we're using it twice let's create an intermediate
[97:10] twice let's create an intermediate variable e
[97:12] variable e and then define o as
[97:14] and then define o as e plus one over
[97:16] e plus one over e minus one over e plus one
[97:19] e minus one over e plus one e minus one over e plus one
[97:22] e minus one over e plus one and that should be it and then we should
[97:24] and that should be it and then we should be able to draw that of o
[97:26] be able to draw that of o so now before i run this what do we
[97:29] so now before i run this what do we expect to see
[97:30] expect to see number one we're expecting to see a much
[97:32] number one we're expecting to see a much longer
[97:33] longer graph here because we've broken up 10h
[97:35] graph here because we've broken up 10h into a bunch of other operations
[97:37] into a bunch of other operations but those operations are mathematically
[97:39] but those operations are mathematically equivalent and so what we're expecting
[97:41] equivalent and so what we're expecting to see is number one the same
[97:43] to see is number one the same result here so the forward pass works
[97:45] result here so the forward pass works and number two because of that
[97:47] and number two because of that mathematical equivalence we expect to
[97:49] mathematical equivalence we expect to see the same backward pass and the same
[97:51] see the same backward pass and the same gradients on these leaf nodes so these
[97:53] gradients on these leaf nodes so these gradients should be identical
[97:55] gradients should be identical so let's run this
[97:58] so let's run this so number one let's verify that instead
[98:00] so number one let's verify that instead of a single 10h node we have now x and
[98:03] of a single 10h node we have now x and we have plus we have times negative one
[98:06] we have plus we have times negative one uh this is the division
[98:08] uh this is the division and we end up with the same forward pass
[98:10] and we end up with the same forward pass here
[98:11] here and then the gradients we have to be
[98:13] and then the gradients we have to be careful because they're in slightly
[98:14] careful because they're in slightly different order potentially the
[98:16] different order potentially the gradients for w2x2 should be 0 and 0.5
[98:19] gradients for w2x2 should be 0 and 0.5 w2 and x2 are 0 and 0.5
[98:22] w2 and x2 are 0 and 0.5 and w1 x1 are 1 and negative 1.5
[98:25] and w1 x1 are 1 and negative 1.5 1 and negative 1.5
[98:27] 1 and negative 1.5 so that means that both our forward
[98:28] so that means that both our forward passes and backward passes were correct
[98:31] passes and backward passes were correct because this turned out to be equivalent
[98:33] because this turned out to be equivalent to
[98:34] to 10h before
[98:35] 10h before and so the reason i wanted to go through
[98:37] and so the reason i wanted to go through this exercise is number one we got to
[98:39] this exercise is number one we got to practice a few more operations and uh
[98:41] practice a few more operations and uh writing more backwards passes and number
[98:43] writing more backwards passes and number two i wanted to illustrate the point
[98:45] two i wanted to illustrate the point that
[98:46] that the um
[98:47] the um the level at which you implement your
[98:49] the level at which you implement your operations is totally up to you you can
[98:51] operations is totally up to you you can implement backward passes for tiny
[98:53] implement backward passes for tiny expressions like a single individual
[98:54] expressions like a single individual plus or a single times
[98:56] plus or a single times or you can implement them for say
[98:58] or you can implement them for say 10h
[99:00] 10h which is a kind of a potentially you can
[99:01] which is a kind of a potentially you can see it as a composite operation because
[99:03] see it as a composite operation because it's made up of all these more atomic
[99:05] it's made up of all these more atomic operations but really all of this is
[99:07] operations but really all of this is kind of like a fake concept all that
[99:08] kind of like a fake concept all that matters is we have some kind of inputs
[99:10] matters is we have some kind of inputs and some kind of an output and this
[99:11] and some kind of an output and this output is a function of the inputs in
[99:13] output is a function of the inputs in some way and as long as you can do
[99:14] some way and as long as you can do forward pass and the backward pass of
[99:16] forward pass and the backward pass of that little operation it doesn't matter
[99:19] that little operation it doesn't matter what that operation is
[99:21] what that operation is and how composite it is
[99:23] and how composite it is if you can write the local gradients you
[99:24] if you can write the local gradients you can chain the gradient and you can
[99:26] can chain the gradient and you can continue back propagation so the design
[99:28] continue back propagation so the design of what those functions are is
[99:30] of what those functions are is completely up to you
[99:31] completely up to you so now i would like to show you how you
[99:33] so now i would like to show you how you can do the exact same thing by using a
[99:35] can do the exact same thing by using a modern deep neural network library like
[99:37] modern deep neural network library like for example pytorch which i've roughly
[99:40] for example pytorch which i've roughly modeled micrograd
[99:41] modeled micrograd by
[99:42] by and so
[99:43] and so pytorch is something you would use in
[99:44] pytorch is something you would use in production and i'll show you how you can
[99:46] production and i'll show you how you can do the exact same thing but in pytorch
[99:48] do the exact same thing but in pytorch api so i'm just going to copy paste it
[99:50] api so i'm just going to copy paste it in and walk you through it a little bit
[99:52] in and walk you through it a little bit this is what it looks like
[99:54] this is what it looks like so we're going to import pi torch and
[99:56] so we're going to import pi torch and then we need to define these
[99:59] then we need to define these value objects like we have here
[100:01] value objects like we have here now micrograd is a scalar valued
[100:04] now micrograd is a scalar valued engine so we only have scalar values
[100:07] engine so we only have scalar values like 2.0 but in pi torch everything is
[100:10] like 2.0 but in pi torch everything is based around tensors and like i
[100:11] based around tensors and like i mentioned tensors are just n-dimensional
[100:13] mentioned tensors are just n-dimensional arrays of scalars
[100:15] arrays of scalars so that's why things get a little bit
[100:17] so that's why things get a little bit more complicated here i just need a
[100:19] more complicated here i just need a scalar value to tensor a tensor with
[100:21] scalar value to tensor a tensor with just a single element
[100:23] just a single element but by default when you work with
[100:25] but by default when you work with pytorch you would use um
[100:28] pytorch you would use um more complicated tensors like this so if
[100:30] more complicated tensors like this so if i import pytorch
[100:33] then i can create tensors like this and
[100:36] then i can create tensors like this and this tensor for example is a two by
[100:38] this tensor for example is a two by three array
[100:39] three array of scalar
[100:41] of scalar scalars
[100:42] scalars in a single compact representation so we
[100:45] in a single compact representation so we can check its shape we see that it's a
[100:46] can check its shape we see that it's a two by three array
[100:48] two by three array and so on
[100:49] and so on so this is usually what you would work
[100:50] so this is usually what you would work with um in the actual libraries so here
[100:53] with um in the actual libraries so here i'm creating
[100:55] i'm creating a tensor that has only a single element
[100:58] a tensor that has only a single element 2.0
[101:00] 2.0 and then i'm casting it to be double
[101:03] and then i'm casting it to be double because python is by default using
[101:05] because python is by default using double precision for its floating point
[101:07] double precision for its floating point numbers so i'd like everything to be
[101:08] numbers so i'd like everything to be identical by default the data type of
[101:12] identical by default the data type of these tensors will be float32 so it's
[101:14] these tensors will be float32 so it's only using a single precision float so
[101:16] only using a single precision float so i'm casting it to double
[101:18] i'm casting it to double so that we have float64 just like in
[101:21] so that we have float64 just like in python
[101:22] python so i'm casting to double and then we get
[101:24] so i'm casting to double and then we get something similar to value of two the
[101:28] something similar to value of two the next thing i have to do is because these
[101:29] next thing i have to do is because these are leaf nodes by default pytorch
[101:31] are leaf nodes by default pytorch assumes that they do not require
[101:32] assumes that they do not require gradients so i need to explicitly say
[101:35] gradients so i need to explicitly say that all of these nodes require
[101:36] that all of these nodes require gradients
[101:37] gradients okay so this is going to construct
[101:39] okay so this is going to construct scalar valued one element tensors
[101:43] scalar valued one element tensors make sure that fighters knows that they
[101:44] make sure that fighters knows that they require gradients now by default these
[101:47] require gradients now by default these are set to false by the way because of
[101:48] are set to false by the way because of efficiency reasons because usually you
[101:50] efficiency reasons because usually you would not want gradients for leaf nodes
[101:53] would not want gradients for leaf nodes like the inputs to the network and this
[101:55] like the inputs to the network and this is just trying to be efficient in the
[101:57] is just trying to be efficient in the most common cases
[101:59] most common cases so once we've defined all of our values
[102:01] so once we've defined all of our values in python we can perform arithmetic just
[102:03] in python we can perform arithmetic just like we can here in microgradlend so
[102:06] like we can here in microgradlend so this will just work and then there's a
[102:07] this will just work and then there's a torch.10h also
[102:09] torch.10h also and when we get back is a tensor again
[102:12] and when we get back is a tensor again and we can
[102:13] and we can just like in micrograd it's got a data
[102:15] just like in micrograd it's got a data attribute and it's got grant attributes
[102:18] attribute and it's got grant attributes so these tensor objects just like in
[102:19] so these tensor objects just like in micrograd have a dot data and a dot grad
[102:22] micrograd have a dot data and a dot grad and
[102:23] and the only difference here is that we need
[102:25] the only difference here is that we need to call it that item because otherwise
[102:28] to call it that item because otherwise um pi torch
[102:30] um pi torch that item basically takes
[102:32] that item basically takes a single tensor of one element and it
[102:34] a single tensor of one element and it just returns that element stripping out
[102:36] just returns that element stripping out the tensor
[102:37] the tensor so let me just run this and hopefully we
[102:39] so let me just run this and hopefully we are going to get this is going to print
[102:41] are going to get this is going to print the forward pass
[102:42] the forward pass which is 0.707
[102:44] which is 0.707 and this will be the gradients which
[102:46] and this will be the gradients which hopefully are
[102:48] hopefully are 0.5 0 negative 1.5 and 1.
[102:51] 0.5 0 negative 1.5 and 1. so if we just run this
[102:53] so if we just run this there we go
[102:54] there we go 0.7 so the forward pass agrees and then
[102:57] 0.7 so the forward pass agrees and then point five zero negative one point five
[102:59] point five zero negative one point five and one
[103:00] and one so pi torch agrees with us
[103:02] so pi torch agrees with us and just to show you here basically o
[103:05] and just to show you here basically o here's a tensor with a single element
[103:08] here's a tensor with a single element and it's a double
[103:09] and it's a double and we can call that item on it to just
[103:12] and we can call that item on it to just get the single number out
[103:14] get the single number out so that's what item does and o is a
[103:16] so that's what item does and o is a tensor object like i mentioned and it's
[103:18] tensor object like i mentioned and it's got a backward function just like we've
[103:20] got a backward function just like we've implemented
[103:22] implemented and then all of these also have a dot
[103:23] and then all of these also have a dot graph so like x2 for example in the grad
[103:26] graph so like x2 for example in the grad and it's a tensor and we can pop out the
[103:28] and it's a tensor and we can pop out the individual number with that actin
[103:31] individual number with that actin so basically
[103:32] so basically torches torch can do what we did in
[103:35] torches torch can do what we did in micrograph is a special case when your
[103:37] micrograph is a special case when your tensors are all single element tensors
[103:40] tensors are all single element tensors but the big deal with pytorch is that
[103:42] but the big deal with pytorch is that everything is significantly more
[103:43] everything is significantly more efficient because we are working with
[103:45] efficient because we are working with these tensor objects and we can do lots
[103:47] these tensor objects and we can do lots of operations in parallel on all of
[103:49] of operations in parallel on all of these tensors
[103:51] these tensors but otherwise what we've built very much
[103:53] but otherwise what we've built very much agrees with the api of pytorch
[103:55] agrees with the api of pytorch okay so now that we have some machinery
[103:57] okay so now that we have some machinery to build out pretty complicated
[103:58] to build out pretty complicated mathematical expressions we can also
[104:00] mathematical expressions we can also start building out neural nets and as i
[104:02] start building out neural nets and as i mentioned neural nets are just a
[104:03] mentioned neural nets are just a specific class of mathematical
[104:05] specific class of mathematical expressions
[104:07] expressions so we're going to start building out a
[104:08] so we're going to start building out a neural net piece by piece and eventually
[104:09] neural net piece by piece and eventually we'll build out a two-layer multi-layer
[104:12] we'll build out a two-layer multi-layer layer perceptron as it's called and i'll
[104:14] layer perceptron as it's called and i'll show you exactly what that means
[104:15] show you exactly what that means let's start with a single individual
[104:17] let's start with a single individual neuron we've implemented one here but
[104:19] neuron we've implemented one here but here i'm going to implement one that
[104:21] here i'm going to implement one that also subscribes to the pytorch api in
[104:24] also subscribes to the pytorch api in how it designs its neural network
[104:26] how it designs its neural network modules
[104:27] modules so just like we saw that we can like
[104:28] so just like we saw that we can like match the api of pytorch
[104:31] match the api of pytorch on the auto grad side we're going to try
[104:33] on the auto grad side we're going to try to do that on the neural network modules
[104:35] to do that on the neural network modules so here's class neuron
[104:38] so here's class neuron and just for the sake of efficiency i'm
[104:40] and just for the sake of efficiency i'm going to copy paste some sections that
[104:42] going to copy paste some sections that are relatively straightforward
[104:45] are relatively straightforward so the constructor will take
[104:47] so the constructor will take number of inputs to this neuron which is
[104:49] number of inputs to this neuron which is how many inputs come to a neuron so this
[104:52] how many inputs come to a neuron so this one for example has three inputs
[104:55] one for example has three inputs and then it's going to create a weight
[104:57] and then it's going to create a weight there is some random number between
[104:58] there is some random number between negative one and one for every one of
[105:00] negative one and one for every one of those inputs
[105:01] those inputs and a bias that controls the overall
[105:03] and a bias that controls the overall trigger happiness of this neuron
[105:06] trigger happiness of this neuron and then we're going to implement a def
[105:08] and then we're going to implement a def underscore underscore call
[105:11] underscore underscore call of self and x some input x
[105:14] of self and x some input x and really what we don't do here is w
[105:15] and really what we don't do here is w times x plus b
[105:17] times x plus b where w times x here is a dot product
[105:19] where w times x here is a dot product specifically
[105:21] specifically now if you haven't seen
[105:22] now if you haven't seen call
[105:24] call let me just return 0.0 here for now the
[105:26] let me just return 0.0 here for now the way this works now is we can have an x
[105:28] way this works now is we can have an x which is say like 2.0 3.0 then we can
[105:31] which is say like 2.0 3.0 then we can initialize a neuron that is
[105:32] initialize a neuron that is two-dimensional
[105:33] two-dimensional because these are two numbers and then
[105:35] because these are two numbers and then we can feed those two numbers into that
[105:37] we can feed those two numbers into that neuron to get an output
[105:39] neuron to get an output and so when you use this notation n of x
[105:42] and so when you use this notation n of x python will use call
[105:45] python will use call so currently call just return 0.0
[105:50] now we'd like to actually do the forward pass of this neuron instead
[105:54] pass of this neuron instead so we're going to do here first is we
[105:57] so we're going to do here first is we need to basically multiply all of the
[105:58] need to basically multiply all of the elements of w with all of the elements
[106:01] elements of w with all of the elements of x pairwise we need to multiply them
[106:04] of x pairwise we need to multiply them so the first thing we're going to do is
[106:05] so the first thing we're going to do is we're going to zip up
[106:07] we're going to zip up celta w and x
[106:09] celta w and x and in python zip takes two iterators
[106:12] and in python zip takes two iterators and it creates a new iterator that
[106:14] and it creates a new iterator that iterates over the tuples of the
[106:16] iterates over the tuples of the corresponding entries
[106:17] corresponding entries so for example just to show you we can
[106:20] so for example just to show you we can print this list
[106:22] print this list and still return 0.0 here
[106:30] sorry
[106:34] so we see that these w's are paired up with the x's w with x
[106:41] and now what we want to do is
[106:47] for w i x i in
[106:50] for w i x i in we want to multiply w times
[106:52] we want to multiply w times w wi times x i
[106:54] w wi times x i and then we want to sum all of that
[106:56] and then we want to sum all of that together
[106:57] together to come up with an activation
[106:59] to come up with an activation and add also subnet b on top
[107:02] and add also subnet b on top so that's the raw activation and then of
[107:04] so that's the raw activation and then of course we need to pass that through a
[107:05] course we need to pass that through a non-linearity so what we're going to be
[107:07] non-linearity so what we're going to be returning is act.10h
[107:09] returning is act.10h and here's out
[107:12] and here's out so
[107:13] so now we see that we are getting some
[107:14] now we see that we are getting some outputs and we get a different output
[107:16] outputs and we get a different output from a neuron each time because we are
[107:17] from a neuron each time because we are initializing different weights and by
[107:19] initializing different weights and by and biases
[107:21] and biases and then to be a bit more efficient here
[107:22] and then to be a bit more efficient here actually sum by the way takes a second
[107:25] actually sum by the way takes a second optional parameter which is the start
[107:28] optional parameter which is the start and by default the start is zero so
[107:31] and by default the start is zero so these elements of this sum will be added
[107:34] these elements of this sum will be added on top of zero to begin with but
[107:35] on top of zero to begin with but actually we can just start with cell dot
[107:37] actually we can just start with cell dot b
[107:38] b and then we just have an expression like
[107:39] and then we just have an expression like this
[107:45] and then the generator expression here must be parenthesized in python
[107:49] must be parenthesized in python there we go
[107:53] yep so now we can forward a single neuron next up we're going to define a
[107:57] neuron next up we're going to define a layer of neurons so here we have a
[107:59] layer of neurons so here we have a schematic for a mlb
[108:02] schematic for a mlb so we see that these mlps each layer
[108:05] so we see that these mlps each layer this is one layer has actually a number
[108:07] this is one layer has actually a number of neurons and they're not connected to
[108:08] of neurons and they're not connected to each other but all of them are fully
[108:09] each other but all of them are fully connected to the input
[108:11] connected to the input so what is a layer of neurons it's just
[108:13] so what is a layer of neurons it's just it's just a set of neurons evaluated
[108:15] it's just a set of neurons evaluated independently
[108:16] independently so
[108:17] so in the interest of time i'm going to do
[108:20] in the interest of time i'm going to do something fairly straightforward here
[108:23] something fairly straightforward here it's um
[108:25] it's um literally a layer is just a list of
[108:27] literally a layer is just a list of neurons
[108:28] neurons and then how many neurons do we have we
[108:30] and then how many neurons do we have we take that as an input argument here how
[108:32] take that as an input argument here how many neurons do you want in your layer
[108:34] many neurons do you want in your layer number of outputs in this layer
[108:36] number of outputs in this layer and so we just initialize completely
[108:38] and so we just initialize completely independent neurons with this given
[108:40] independent neurons with this given dimensionality and when we call on it we
[108:43] dimensionality and when we call on it we just independently
[108:44] just independently evaluate them so now instead of a neuron
[108:47] evaluate them so now instead of a neuron we can make a layer of neurons they are
[108:49] we can make a layer of neurons they are two-dimensional neurons and let's have
[108:51] two-dimensional neurons and let's have three of them
[108:52] three of them and now we see that we have three
[108:53] and now we see that we have three independent evaluations of three
[108:55] independent evaluations of three different neurons
[108:57] different neurons right
[108:58] right okay finally let's complete this picture
[109:00] okay finally let's complete this picture and define an entire multi-layer
[109:02] and define an entire multi-layer perceptron or mlp
[109:04] perceptron or mlp and as we can see here in an mlp these
[109:06] and as we can see here in an mlp these layers just feed into each other
[109:07] layers just feed into each other sequentially
[109:09] sequentially so let's come here and i'm just going to
[109:11] so let's come here and i'm just going to copy the code here in interest of time
[109:14] copy the code here in interest of time so an mlp is very similar
[109:16] so an mlp is very similar we're taking the number of inputs
[109:18] we're taking the number of inputs as before but now instead of taking a
[109:20] as before but now instead of taking a single n out which is number of neurons
[109:22] single n out which is number of neurons in a single layer we're going to take a
[109:24] in a single layer we're going to take a list of an outs and this list defines
[109:26] list of an outs and this list defines the sizes of all the layers that we want
[109:28] the sizes of all the layers that we want in our mlp
[109:30] in our mlp so here we just put them all together
[109:31] so here we just put them all together and then iterate over consecutive pairs
[109:34] and then iterate over consecutive pairs of these sizes and create layer objects
[109:36] of these sizes and create layer objects for them
[109:37] for them and then in the call function we are
[109:39] and then in the call function we are just calling them sequentially so that's
[109:41] just calling them sequentially so that's an mlp really
[109:42] an mlp really and let's actually re-implement this
[109:44] and let's actually re-implement this picture so we want three input neurons
[109:46] picture so we want three input neurons and then two layers of four and an
[109:48] and then two layers of four and an output unit
[109:49] output unit so
[109:50] so we want
[109:52] we want a three-dimensional input say this is an
[109:54] a three-dimensional input say this is an example input we want three inputs into
[109:57] example input we want three inputs into two layers of four and one output
[110:00] two layers of four and one output and this of course is an mlp
[110:03] and this of course is an mlp and there we go that's a forward pass of
[110:05] and there we go that's a forward pass of an mlp
[110:06] an mlp to make this a little bit nicer you see
[110:08] to make this a little bit nicer you see how we have just a single element but
[110:09] how we have just a single element but it's wrapped in a list because layer
[110:11] it's wrapped in a list because layer always returns lists
[110:13] always returns lists circle for convenience
[110:15] circle for convenience return outs at zero if len out is
[110:18] return outs at zero if len out is exactly a single element
[110:20] exactly a single element else return fullest
[110:22] else return fullest and this will allow us to just get a
[110:23] and this will allow us to just get a single value out at the last layer that
[110:25] single value out at the last layer that only has a single neuron
[110:28] only has a single neuron and finally we should be able to draw
[110:29] and finally we should be able to draw dot of n of x
[110:31] dot of n of x and
[110:32] and as you might imagine
[110:34] as you might imagine these expressions are now getting
[110:36] these expressions are now getting relatively involved
[110:38] relatively involved so this is an entire mlp that we're
[110:40] so this is an entire mlp that we're defining now
[110:45] all the way until a single output
[110:48] all the way until a single output okay
[110:49] okay and so obviously you would never
[110:50] and so obviously you would never differentiate on pen and paper these
[110:52] differentiate on pen and paper these expressions but with micrograd we will
[110:55] expressions but with micrograd we will be able to back propagate all the way
[110:56] be able to back propagate all the way through this
[110:58] through this and back propagate
[110:59] and back propagate into
[111:00] into these weights of all these neurons so
[111:02] these weights of all these neurons so let's see how that works okay so let's
[111:04] let's see how that works okay so let's create ourselves a very simple
[111:06] create ourselves a very simple example data set here
[111:08] example data set here so this data set has four examples
[111:11] so this data set has four examples and so we have four possible
[111:13] and so we have four possible inputs into the neural net
[111:15] inputs into the neural net and we have four desired targets so we'd
[111:17] and we have four desired targets so we'd like the neural net to assign
[111:21] like the neural net to assign or output 1.0 when it's fed this example
[111:24] or output 1.0 when it's fed this example negative one when it's fed these
[111:25] negative one when it's fed these examples and one when it's fed this
[111:26] examples and one when it's fed this example so it's a very simple binary
[111:28] example so it's a very simple binary classifier neural net basically that we
[111:30] classifier neural net basically that we would like here
[111:32] would like here now let's think what the neural net
[111:33] now let's think what the neural net currently thinks about these four
[111:34] currently thinks about these four examples we can just get their
[111:36] examples we can just get their predictions
[111:37] predictions um basically we can just call n of x for
[111:40] um basically we can just call n of x for x in axis
[111:42] x in axis and then we can
[111:43] and then we can print
[111:45] print so these are the outputs of the neural
[111:46] so these are the outputs of the neural net on those four examples
[111:48] net on those four examples so
[111:50] so the first one is 0.91 but we'd like it
[111:52] the first one is 0.91 but we'd like it to be one so we should push this one
[111:55] to be one so we should push this one higher this one we want to be higher
[111:58] higher this one we want to be higher this one says 0.88 and we want this to
[112:00] this one says 0.88 and we want this to be negative one
[112:02] be negative one this is 0.8 we want it to be negative
[112:04] this is 0.8 we want it to be negative one
[112:05] one and this one is 0.8 we want it to be one
[112:08] and this one is 0.8 we want it to be one so how do we make the neural net and how
[112:10] so how do we make the neural net and how do we tune the weights
[112:12] do we tune the weights to
[112:12] to better predict the desired targets
[112:16] better predict the desired targets and the trick used in deep learning to
[112:18] and the trick used in deep learning to achieve this is to
[112:20] achieve this is to calculate a single number that somehow
[112:22] calculate a single number that somehow measures the total performance of your
[112:24] measures the total performance of your neural net and we call this single
[112:25] neural net and we call this single number the loss
[112:28] number the loss so the loss
[112:29] so the loss first
[112:31] first is is a single number that we're going
[112:32] is is a single number that we're going to define that basically measures how
[112:34] to define that basically measures how well the neural net is performing right
[112:36] well the neural net is performing right now we have the intuitive sense that
[112:37] now we have the intuitive sense that it's not performing very well because
[112:38] it's not performing very well because we're not very much close to this
[112:40] we're not very much close to this so the loss will be high and we'll want
[112:43] so the loss will be high and we'll want to minimize the loss
[112:44] to minimize the loss so in particular in this case what we're
[112:46] so in particular in this case what we're going to do is we're going to implement
[112:47] going to do is we're going to implement the mean squared error loss
[112:49] the mean squared error loss so this is doing is we're going to
[112:51] so this is doing is we're going to basically iterate um
[112:54] basically iterate um for y ground truth
[112:56] for y ground truth and y output in zip of um
[112:59] and y output in zip of um wise and white red so we're going to
[113:01] wise and white red so we're going to pair up the
[113:03] pair up the ground truths with the predictions
[113:06] ground truths with the predictions and this zip iterates over tuples of
[113:07] and this zip iterates over tuples of them
[113:08] them and for each
[113:11] and for each y ground truth and y output we're going
[113:13] y ground truth and y output we're going to subtract them
[113:16] and square them so let's first see what these losses are
[113:20] so let's first see what these losses are these are individual loss components
[113:22] these are individual loss components and so basically for each
[113:25] and so basically for each one of the four
[113:26] one of the four we are taking the prediction and the
[113:28] we are taking the prediction and the ground truth we are subtracting them and
[113:30] ground truth we are subtracting them and squaring them
[113:32] squaring them so because
[113:33] so because this one is so close to its target 0.91
[113:36] this one is so close to its target 0.91 is almost one
[113:38] is almost one subtracting them gives a very small
[113:40] subtracting them gives a very small number
[113:41] number so here we would get like a negative
[113:43] so here we would get like a negative point one and then squaring it
[113:45] point one and then squaring it just makes sure
[113:47] just makes sure that regardless of whether we are more
[113:49] that regardless of whether we are more negative or more positive we always get
[113:51] negative or more positive we always get a positive
[113:52] a positive number instead of squaring we should we
[113:55] number instead of squaring we should we could also take for example the absolute
[113:56] could also take for example the absolute value we need to discard the sign
[113:59] value we need to discard the sign and so you see that the expression is
[114:00] and so you see that the expression is ranged so that you only get zero exactly
[114:03] ranged so that you only get zero exactly when y out is equal to y ground truth
[114:06] when y out is equal to y ground truth when those two are equal so your
[114:07] when those two are equal so your prediction is exactly the target you are
[114:09] prediction is exactly the target you are going to get zero
[114:10] going to get zero and if your prediction is not the target
[114:12] and if your prediction is not the target you are going to get some other number
[114:15] you are going to get some other number so here for example we are way off and
[114:17] so here for example we are way off and so that's why the loss is quite high
[114:19] so that's why the loss is quite high and the more off we are the greater the
[114:22] and the more off we are the greater the loss will be
[114:24] loss will be so we don't want high loss we want low
[114:26] so we don't want high loss we want low loss
[114:27] loss and so the final loss here will be just
[114:30] and so the final loss here will be just the sum
[114:32] the sum of all of these
[114:33] of all of these numbers
[114:34] numbers so you see that this should be zero
[114:36] so you see that this should be zero roughly plus zero roughly
[114:38] roughly plus zero roughly but plus
[114:39] but plus seven
[114:40] seven so loss should be about seven
[114:43] so loss should be about seven here
[114:44] here and now we want to minimize the loss we
[114:47] and now we want to minimize the loss we want the loss to be low
[114:49] want the loss to be low because if loss is low
[114:51] because if loss is low then every one of the predictions is
[114:54] then every one of the predictions is equal to its target
[114:56] equal to its target so the loss the lowest it can be is zero
[114:58] so the loss the lowest it can be is zero and the greater it is the worse off the
[115:01] and the greater it is the worse off the neural net is predicting
[115:04] neural net is predicting so now of course if we do lost that
[115:05] so now of course if we do lost that backward
[115:07] backward something magical happened when i hit
[115:09] something magical happened when i hit enter
[115:10] enter and the magical thing of course that
[115:12] and the magical thing of course that happened is that we can look at
[115:14] happened is that we can look at end.layers.neuron and that layers at say
[115:16] end.layers.neuron and that layers at say like the the first layer
[115:18] like the the first layer that neurons at zero
[115:22] because remember that mlp has the layers which is a list
[115:26] which is a list and each layer has a neurons which is a
[115:28] and each layer has a neurons which is a list and that gives us an individual
[115:29] list and that gives us an individual neuron
[115:30] neuron and then it's got some weights
[115:32] and then it's got some weights and so we can for example look at the
[115:34] and so we can for example look at the weights at zero
[115:38] um oops it's not called weights it's called
[115:42] oops it's not called weights it's called w
[115:44] w and that's a value but now this value
[115:46] and that's a value but now this value also has a groud because of the backward
[115:48] also has a groud because of the backward pass
[115:50] pass and so we see that because this gradient
[115:52] and so we see that because this gradient here on this particular weight of this
[115:54] here on this particular weight of this particular neuron of this particular
[115:56] particular neuron of this particular layer is negative
[115:57] layer is negative we see that its influence on the loss is
[116:00] we see that its influence on the loss is also negative so slightly increasing
[116:02] also negative so slightly increasing this particular weight of this neuron of
[116:04] this particular weight of this neuron of this layer would make the loss go down
[116:08] this layer would make the loss go down and we actually have this information
[116:10] and we actually have this information for every single one of our neurons and
[116:12] for every single one of our neurons and all their parameters actually it's worth
[116:13] all their parameters actually it's worth looking at also the draw dot loss by the
[116:16] looking at also the draw dot loss by the way
[116:17] way so previously we looked at the draw dot
[116:19] so previously we looked at the draw dot of a single neural neuron forward pass
[116:21] of a single neural neuron forward pass and that was already a large expression
[116:23] and that was already a large expression but what is this expression we actually
[116:25] but what is this expression we actually forwarded
[116:27] forwarded every one of those four examples and
[116:29] every one of those four examples and then we have the loss on top of them
[116:30] then we have the loss on top of them with the mean squared error
[116:32] with the mean squared error and so this is a really massive graph
[116:36] and so this is a really massive graph because this graph that we've built up
[116:38] because this graph that we've built up now
[116:39] now oh my gosh this graph that we've built
[116:41] oh my gosh this graph that we've built up now
[116:42] up now which is kind of excessive it's
[116:44] which is kind of excessive it's excessive because it has four forward
[116:46] excessive because it has four forward passes of a neural net for every one of
[116:48] passes of a neural net for every one of the examples and then it has the loss on
[116:50] the examples and then it has the loss on top
[116:51] top and it ends with the value of the loss
[116:53] and it ends with the value of the loss which was 7.12
[116:55] which was 7.12 and this loss will now back propagate
[116:56] and this loss will now back propagate through all the four forward passes all
[116:58] through all the four forward passes all the way through just every single
[117:00] the way through just every single intermediate value of the neural net
[117:03] intermediate value of the neural net all the way back to of course the
[117:05] all the way back to of course the parameters of the weights which are the
[117:06] parameters of the weights which are the input
[117:07] input so these weight parameters here are
[117:10] so these weight parameters here are inputs to this neural net
[117:12] inputs to this neural net and
[117:13] and these numbers here these scalars are
[117:15] these numbers here these scalars are inputs to the neural net
[117:16] inputs to the neural net so if we went around here
[117:18] so if we went around here we'll probably find
[117:20] we'll probably find some of these examples this 1.0
[117:22] some of these examples this 1.0 potentially maybe this 1.0 or you know
[117:25] potentially maybe this 1.0 or you know some of the others and you'll see that
[117:26] some of the others and you'll see that they all have gradients as well
[117:28] they all have gradients as well the thing is these gradients on the
[117:30] the thing is these gradients on the input data are not that useful to us
[117:33] input data are not that useful to us and that's because the input data seems
[117:36] and that's because the input data seems to be not changeable it's it's a given
[117:38] to be not changeable it's it's a given to the problem and so it's a fixed input
[117:40] to the problem and so it's a fixed input we're not going to be changing it or
[117:42] we're not going to be changing it or messing with it even though we do have
[117:43] messing with it even though we do have gradients for it
[117:46] gradients for it but some of these gradients here
[117:49] but some of these gradients here will be for the neural network
[117:50] will be for the neural network parameters the ws and the bs and those
[117:53] parameters the ws and the bs and those we of course we want to change
[117:55] we of course we want to change okay so now we're going to want some
[117:58] okay so now we're going to want some convenience code to gather up all of the
[117:59] convenience code to gather up all of the parameters of the neural net so that we
[118:01] parameters of the neural net so that we can operate on all of them
[118:03] can operate on all of them simultaneously and every one of them we
[118:05] simultaneously and every one of them we will nudge a tiny amount
[118:08] will nudge a tiny amount based on the gradient information
[118:10] based on the gradient information so let's collect the parameters of the
[118:11] so let's collect the parameters of the neural net all in one array
[118:14] neural net all in one array so let's create a parameters of self
[118:17] so let's create a parameters of self that just
[118:18] that just returns celta w which is a list
[118:22] returns celta w which is a list concatenated with
[118:24] concatenated with a list of self.b
[118:27] a list of self.b so this will just return a list
[118:29] so this will just return a list list plus list just you know gives you a
[118:31] list plus list just you know gives you a list
[118:32] list so that's parameters of neuron and i'm
[118:35] so that's parameters of neuron and i'm calling it this way because also pi
[118:36] calling it this way because also pi torch has a parameters on every single
[118:38] torch has a parameters on every single and in module
[118:40] and in module and uh it does exactly what we're doing
[118:42] and uh it does exactly what we're doing here it just returns the
[118:44] here it just returns the parameter tensors for us as the
[118:46] parameter tensors for us as the parameter scalars
[118:48] parameter scalars now layer is also a module so it will
[118:50] now layer is also a module so it will have parameters
[118:52] have parameters itself
[118:54] itself and basically what we want to do here is
[118:56] and basically what we want to do here is something like this like
[119:00] params is here and then for
[119:03] params is here and then for neuron in salt out neurons
[119:07] neuron in salt out neurons we want to get neuron.parameters
[119:10] we want to get neuron.parameters and we want to params.extend
[119:13] and we want to params.extend right so these are the parameters of
[119:16] right so these are the parameters of this neuron and then we want to put them
[119:17] this neuron and then we want to put them on top of params so params dot extend
[119:21] on top of params so params dot extend of peace
[119:22] of peace and then we want to return brands
[119:25] and then we want to return brands so this is way too much code so actually
[119:28] so this is way too much code so actually there's a way to simplify this which is
[119:31] there's a way to simplify this which is return
[119:33] return p
[119:35] p for neuron in self
[119:38] for neuron in self neurons
[119:39] neurons for
[119:41] for p in neuron dot parameters
[119:45] p in neuron dot parameters so it's a single list comprehension in
[119:47] so it's a single list comprehension in python you can sort of nest them like
[119:49] python you can sort of nest them like this and you can um
[119:51] this and you can um then create
[119:52] then create uh the desired
[119:54] uh the desired array so this is these are identical
[119:57] array so this is these are identical we can take this out
[120:00] we can take this out and then let's do the same here
[120:04] def parameters self
[120:07] self and return
[120:09] and return a parameter for layer in self dot layers
[120:13] a parameter for layer in self dot layers for
[120:15] for p in layer dot parameters
[120:20] and that should be good
[120:23] and that should be good now let me pop out this so
[120:26] now let me pop out this so we don't re-initialize our network
[120:28] we don't re-initialize our network because we need to re-initialize
[120:31] because we need to re-initialize our
[120:35] okay so unfortunately we will have to probably re-initialize the network
[120:38] probably re-initialize the network because we just add functionality
[120:41] because we just add functionality because this class of course we i want
[120:43] because this class of course we i want to get all the and that parameters but
[120:45] to get all the and that parameters but that's not going to work because this is
[120:47] that's not going to work because this is the old class
[120:49] the old class okay
[120:50] okay so unfortunately we do have to
[120:52] so unfortunately we do have to reinitialize the network which will
[120:53] reinitialize the network which will change some of the numbers
[120:55] change some of the numbers but let me do that so that we pick up
[120:57] but let me do that so that we pick up the new api we can now do in the
[120:58] the new api we can now do in the parameters
[121:00] parameters and these are all the weights and biases
[121:02] and these are all the weights and biases inside the entire neural net
[121:05] inside the entire neural net so in total this mlp has 41 parameters
[121:11] and now we'll be able to change them
[121:15] now we'll be able to change them if we recalculate the loss here we see
[121:18] if we recalculate the loss here we see that unfortunately we have slightly
[121:19] that unfortunately we have slightly different
[121:22] different predictions and slightly different laws
[121:26] but that's okay okay so we see that this neurons
[121:31] okay so we see that this neurons gradient is slightly negative we can
[121:33] gradient is slightly negative we can also look at its data right now
[121:36] also look at its data right now which is 0.85 so this is the current
[121:38] which is 0.85 so this is the current value of this neuron and this is its
[121:40] value of this neuron and this is its gradient on the loss
[121:43] gradient on the loss so what we want to do now is we want to
[121:45] so what we want to do now is we want to iterate for every p in
[121:47] iterate for every p in n dot parameters so for all the 41
[121:49] n dot parameters so for all the 41 parameters in this neural net
[121:51] parameters in this neural net we actually want to change p data
[121:55] we actually want to change p data slightly
[121:56] slightly according to the gradient information
[121:59] according to the gradient information okay so
[122:00] okay so dot dot to do here
[122:02] dot dot to do here but this will be basically a tiny update
[122:05] but this will be basically a tiny update in this gradient descent scheme in
[122:08] in this gradient descent scheme in gradient descent we are thinking of the
[122:10] gradient descent we are thinking of the gradient as a vector pointing in the
[122:13] gradient as a vector pointing in the direction
[122:14] direction of
[122:15] of increased
[122:16] increased loss
[122:19] loss and so
[122:20] and so in gradient descent we are modifying
[122:22] in gradient descent we are modifying p data
[122:24] p data by a small step size in the direction of
[122:26] by a small step size in the direction of the gradient so the step size as an
[122:28] the gradient so the step size as an example could be like a very small
[122:29] example could be like a very small number like 0.01 is the step size times
[122:32] number like 0.01 is the step size times p dot grad
[122:35] p dot grad right
[122:36] right but we have to think through some of the
[122:37] but we have to think through some of the signs here
[122:38] signs here so uh
[122:40] so uh in particular working with this specific
[122:43] in particular working with this specific example here
[122:44] example here we see that if we just left it like this
[122:47] we see that if we just left it like this then this neuron's value
[122:49] then this neuron's value would be currently increased by a tiny
[122:51] would be currently increased by a tiny amount of the gradient
[122:53] amount of the gradient the grain is negative so this value of
[122:56] the grain is negative so this value of this neuron would go slightly down it
[122:58] this neuron would go slightly down it would become like 0.8 you know four or
[123:00] would become like 0.8 you know four or something like that
[123:02] something like that but if this neuron's value goes lower
[123:06] but if this neuron's value goes lower that would actually
[123:08] that would actually increase the loss
[123:10] increase the loss that's because
[123:12] that's because the derivative of this neuron is
[123:14] the derivative of this neuron is negative so increasing
[123:16] negative so increasing this makes the loss go down so
[123:19] this makes the loss go down so increasing it is what we want to do
[123:21] increasing it is what we want to do instead of decreasing it so basically
[123:23] instead of decreasing it so basically what we're missing here is we're
[123:24] what we're missing here is we're actually missing a negative sign
[123:26] actually missing a negative sign and again this other interpretation
[123:29] and again this other interpretation and that's because we want to minimize
[123:30] and that's because we want to minimize the loss we don't want to maximize the
[123:31] the loss we don't want to maximize the loss we want to decrease it
[123:33] loss we want to decrease it and the other interpretation as i
[123:34] and the other interpretation as i mentioned is you can think of the
[123:36] mentioned is you can think of the gradient vector
[123:37] gradient vector so basically just the vector of all the
[123:39] so basically just the vector of all the gradients
[123:40] gradients as pointing in the direction of
[123:42] as pointing in the direction of increasing
[123:44] increasing the loss but then we want to decrease it
[123:46] the loss but then we want to decrease it so we actually want to go in the
[123:47] so we actually want to go in the opposite direction
[123:49] opposite direction and so you can convince yourself that
[123:50] and so you can convince yourself that this sort of plug does the right thing
[123:51] this sort of plug does the right thing here with the negative because we want
[123:53] here with the negative because we want to minimize the loss
[123:55] to minimize the loss so if we nudge all the parameters by
[123:57] so if we nudge all the parameters by tiny amount
[124:00] then we'll see that this data will have changed a little bit
[124:04] this data will have changed a little bit so now this neuron
[124:06] so now this neuron is a tiny amount greater
[124:08] is a tiny amount greater value so 0.854 went to 0.857
[124:13] value so 0.854 went to 0.857 and that's a good thing because slightly
[124:16] and that's a good thing because slightly increasing this neuron
[124:18] increasing this neuron uh
[124:18] uh data makes the loss go down according to
[124:21] data makes the loss go down according to the gradient and so the correct thing
[124:23] the gradient and so the correct thing has happened sign wise
[124:26] has happened sign wise and so now what we would expect of
[124:27] and so now what we would expect of course is that
[124:29] course is that because we've changed all these
[124:30] because we've changed all these parameters we expect that the loss
[124:32] parameters we expect that the loss should have gone down a bit
[124:35] should have gone down a bit so we want to re-evaluate the loss let
[124:37] so we want to re-evaluate the loss let me basically
[124:39] this is just a data definition that hasn't changed but the forward pass here
[124:44] hasn't changed but the forward pass here of the network we can recalculate
[124:49] and actually let me do it outside here so that we can compare the two loss
[124:52] so that we can compare the two loss values
[124:54] values so here if i recalculate the loss
[124:57] so here if i recalculate the loss we'd expect the new loss now to be
[124:59] we'd expect the new loss now to be slightly lower than this number so
[125:01] slightly lower than this number so hopefully what we're getting now is a
[125:03] hopefully what we're getting now is a tiny bit lower than 4.84
[125:06] tiny bit lower than 4.84 4.36
[125:08] 4.36 okay and remember the way we've arranged
[125:10] okay and remember the way we've arranged this is that low loss means that our
[125:12] this is that low loss means that our predictions are matching the targets so
[125:15] predictions are matching the targets so our predictions now are probably
[125:16] our predictions now are probably slightly closer to the
[125:18] slightly closer to the targets and now all we have to do is we
[125:22] targets and now all we have to do is we have to iterate this process
[125:24] have to iterate this process so again um we've done the forward pass
[125:26] so again um we've done the forward pass and this is the loss
[125:28] and this is the loss now we can lost that backward
[125:30] now we can lost that backward let me take these out and we can do a
[125:32] let me take these out and we can do a step size
[125:34] step size and now we should have a slightly lower
[125:35] and now we should have a slightly lower loss 4.36 goes to 3.9
[125:39] loss 4.36 goes to 3.9 and okay so
[125:41] and okay so we've done the forward pass here's the
[125:43] we've done the forward pass here's the backward pass
[125:44] backward pass nudge
[125:45] nudge and now the loss is 3.66
[125:50] 3.47 and you get the idea we just continue
[125:54] and you get the idea we just continue doing this and this is uh gradient
[125:56] doing this and this is uh gradient descent we're just iteratively doing
[125:58] descent we're just iteratively doing forward pass backward pass update
[126:01] forward pass backward pass update forward pass backward pass update and
[126:02] forward pass backward pass update and the neural net is improving its
[126:04] the neural net is improving its predictions
[126:05] predictions so here if we look at why pred now
[126:09] so here if we look at why pred now like red
[126:12] we see that um this value should be getting closer to
[126:15] this value should be getting closer to one
[126:16] one so this value should be getting more
[126:17] so this value should be getting more positive these should be getting more
[126:19] positive these should be getting more negative and this one should be also
[126:20] negative and this one should be also getting more positive so if we just
[126:22] getting more positive so if we just iterate this
[126:23] iterate this a few more times
[126:26] actually we may be able to afford go to go a bit faster let's try a slightly
[126:30] go a bit faster let's try a slightly higher learning rate
[126:34] oops okay there we go so now we're at 0.31
[126:39] if you go too fast by the way if you try to make it too big of a step you may
[126:43] to make it too big of a step you may actually overstep
[126:47] it's overconfidence because again remember we don't actually know exactly
[126:50] remember we don't actually know exactly about the loss function the loss
[126:51] about the loss function the loss function has all kinds of structure and
[126:53] function has all kinds of structure and we only know about the very local
[126:55] we only know about the very local dependence of all these parameters on
[126:57] dependence of all these parameters on the loss but if we step too far
[126:59] the loss but if we step too far we may step into you know a part of the
[127:01] we may step into you know a part of the loss that is completely different
[127:03] loss that is completely different and that can destabilize training and
[127:04] and that can destabilize training and make your loss actually blow up even
[127:08] make your loss actually blow up even so the loss is now 0.04 so actually the
[127:11] so the loss is now 0.04 so actually the predictions should be really quite close
[127:13] predictions should be really quite close let's take a look
[127:15] let's take a look so you see how this is almost one
[127:17] so you see how this is almost one almost negative one almost one we can
[127:19] almost negative one almost one we can continue going
[127:21] continue going uh so
[127:22] uh so yep backward
[127:24] yep backward update
[127:25] update oops there we go so we went way too fast
[127:28] oops there we go so we went way too fast and um
[127:29] and um we actually overstepped
[127:31] we actually overstepped so we got two uh too eager where are we
[127:34] so we got two uh too eager where are we now oops
[127:36] now oops okay
[127:37] okay seven e negative nine so this is very
[127:39] seven e negative nine so this is very very low loss
[127:41] very low loss and the predictions
[127:43] and the predictions are basically perfect
[127:45] are basically perfect so somehow we
[127:47] so somehow we basically we were doing way too big
[127:48] basically we were doing way too big updates and we briefly exploded but then
[127:50] updates and we briefly exploded but then somehow we ended up getting into a
[127:51] somehow we ended up getting into a really good spot so usually this
[127:54] really good spot so usually this learning rate and the tuning of it is a
[127:56] learning rate and the tuning of it is a subtle art you want to set your learning
[127:58] subtle art you want to set your learning rate if it's too low you're going to
[128:00] rate if it's too low you're going to take way too long to converge but if
[128:02] take way too long to converge but if it's too high the whole thing gets
[128:03] it's too high the whole thing gets unstable and you might actually even
[128:05] unstable and you might actually even explode the loss
[128:07] explode the loss depending on your loss function
[128:08] depending on your loss function so finding the step size to be just
[128:10] so finding the step size to be just right it's it's a pretty subtle art
[128:12] right it's it's a pretty subtle art sometimes when you're using sort of
[128:14] sometimes when you're using sort of vanilla gradient descent
[128:15] vanilla gradient descent but we happen to get into a good spot we
[128:17] but we happen to get into a good spot we can look at
[128:19] can look at n-dot parameters
[128:22] n-dot parameters so this is the setting of weights and
[128:25] so this is the setting of weights and biases
[128:26] biases that makes our network
[128:29] that makes our network predict
[128:30] predict the desired targets
[128:31] the desired targets very very close
[128:33] very very close and
[128:35] and basically we've successfully trained
[128:37] basically we've successfully trained neural net
[128:38] neural net okay let's make this a tiny bit more
[128:40] okay let's make this a tiny bit more respectable and implement an actual
[128:41] respectable and implement an actual training loop and what that looks like
[128:43] training loop and what that looks like so this is the data definition that
[128:45] so this is the data definition that stays this is the forward pass
[128:47] stays this is the forward pass um so
[128:49] um so for uh k in range you know we're going
[128:52] for uh k in range you know we're going to
[128:53] to take a bunch of steps
[128:57] first you do the forward pass
[129:00] first you do the forward pass we validate the loss
[129:03] let's re-initialize the neural net from scratch
[129:06] scratch and here's the data
[129:08] and here's the data and we first do before pass then we do
[129:11] and we first do before pass then we do the backward pass
[129:19] and then we do an update that's gradient descent
[129:26] and then we should be able to iterate this and we should be able to print the
[129:29] this and we should be able to print the current step
[129:30] current step the current loss um let's just print the
[129:33] the current loss um let's just print the sort of
[129:34] sort of number of the loss
[129:36] number of the loss and
[129:38] and that should be it
[129:40] that should be it and then the learning rate 0.01 is a
[129:42] and then the learning rate 0.01 is a little too small 0.1 we saw is like a
[129:44] little too small 0.1 we saw is like a little bit dangerously too high let's go
[129:46] little bit dangerously too high let's go somewhere in between
[129:47] somewhere in between and we'll optimize this for
[129:50] and we'll optimize this for not 10 steps but let's go for say 20
[129:52] not 10 steps but let's go for say 20 steps
[129:54] steps let me erase all of this junk
[129:59] and uh let's run the optimization
[130:03] and you see how we've actually converged slower in a more controlled manner and
[130:08] slower in a more controlled manner and got to a loss that is very low
[130:11] got to a loss that is very low so
[130:12] so i expect white bread to be quite good
[130:15] i expect white bread to be quite good there we go
[130:19] um
[130:22] um and
[130:23] and that's it
[130:24] that's it okay so this is kind of embarrassing but
[130:25] okay so this is kind of embarrassing but we actually have a really terrible bug
[130:28] we actually have a really terrible bug in here and it's a subtle bug and it's a
[130:31] in here and it's a subtle bug and it's a very common bug and i can't believe i've
[130:33] very common bug and i can't believe i've done it for the 20th time in my life
[130:36] done it for the 20th time in my life especially on camera and i could have
[130:38] especially on camera and i could have reshot the whole thing but i think it's
[130:39] reshot the whole thing but i think it's pretty funny and you know you get to
[130:41] pretty funny and you know you get to appreciate a bit what um working with
[130:44] appreciate a bit what um working with neural nets maybe
[130:45] neural nets maybe is like sometimes
[130:47] is like sometimes we are guilty of
[130:50] we are guilty of come bug i've actually tweeted
[130:52] come bug i've actually tweeted the most common neural net mistakes a
[130:54] the most common neural net mistakes a long time ago now
[130:56] long time ago now uh and
[130:57] uh and i'm not really
[130:59] i'm not really gonna explain any of these except for we
[131:01] gonna explain any of these except for we are guilty of number three you forgot to
[131:03] are guilty of number three you forgot to zero grad
[131:04] zero grad before that backward what is that
[131:09] basically what's happening and it's a subtle bug and i'm not sure if you saw
[131:12] subtle bug and i'm not sure if you saw it
[131:12] it is that
[131:14] is that all of these
[131:15] all of these weights here have a dot data and a dot
[131:17] weights here have a dot data and a dot grad
[131:19] grad and that grad starts at zero
[131:22] and that grad starts at zero and then we do backward and we fill in
[131:24] and then we do backward and we fill in the gradients
[131:25] the gradients and then we do an update on the data but
[131:27] and then we do an update on the data but we don't flush the grad
[131:29] we don't flush the grad it stays there
[131:31] it stays there so when we do the second
[131:33] so when we do the second forward pass and we do backward again
[131:35] forward pass and we do backward again remember that all the backward
[131:36] remember that all the backward operations do a plus equals on the grad
[131:39] operations do a plus equals on the grad and so these gradients just
[131:41] and so these gradients just add up and they never get reset to zero
[131:44] add up and they never get reset to zero so basically we didn't zero grad so
[131:47] so basically we didn't zero grad so here's how we zero grad before
[131:50] here's how we zero grad before backward
[131:51] backward we need to iterate over all the
[131:52] we need to iterate over all the parameters
[131:54] parameters and we need to make sure that p dot grad
[131:56] and we need to make sure that p dot grad is set to zero
[131:58] is set to zero we need to reset it to zero just like it
[132:00] we need to reset it to zero just like it is in the constructor
[132:02] is in the constructor so remember all the way here for all
[132:04] so remember all the way here for all these value nodes grad is reset to zero
[132:07] these value nodes grad is reset to zero and then all these backward passes do a
[132:09] and then all these backward passes do a plus equals from that grad
[132:11] plus equals from that grad but we need to make sure that
[132:13] but we need to make sure that we reset these graphs to zero so that
[132:15] we reset these graphs to zero so that when we do backward
[132:17] when we do backward all of them start at zero and the actual
[132:18] all of them start at zero and the actual backward pass accumulates um
[132:21] backward pass accumulates um the loss derivatives into the grads
[132:25] the loss derivatives into the grads so this is zero grad in pytorch
[132:28] so this is zero grad in pytorch and uh
[132:30] and uh we will slightly get we'll get a
[132:31] we will slightly get we'll get a slightly different optimization let's
[132:33] slightly different optimization let's reset the neural net
[132:34] reset the neural net the data is the same this is now i think
[132:37] the data is the same this is now i think correct
[132:38] correct and we get a much more
[132:40] and we get a much more you know we get a much more
[132:42] you know we get a much more slower descent
[132:44] slower descent we still end up with pretty good results
[132:46] we still end up with pretty good results and we can continue this a bit more
[132:48] and we can continue this a bit more to get down lower
[132:50] to get down lower and lower
[132:51] and lower and lower
[132:54] yeah so the only reason that the previous
[132:57] so the only reason that the previous thing worked it's extremely buggy um the
[132:59] thing worked it's extremely buggy um the only reason that worked is that
[133:03] only reason that worked is that this is a very very simple problem
[133:05] this is a very very simple problem and it's very easy for this neural net
[133:07] and it's very easy for this neural net to fit this data
[133:09] to fit this data and so the grads ended up accumulating
[133:12] and so the grads ended up accumulating and it effectively gave us a massive
[133:13] and it effectively gave us a massive step size and it made us converge
[133:16] step size and it made us converge extremely fast
[133:19] but basically now we have to do more steps to get to very low values of loss
[133:24] steps to get to very low values of loss and get wipe red to be really good we
[133:26] and get wipe red to be really good we can try to
[133:27] can try to step a bit greater
[133:34] yeah we're gonna get closer and closer to one minus one and one
[133:38] to one minus one and one so
[133:39] so working with neural nets is sometimes
[133:41] working with neural nets is sometimes tricky because
[133:43] tricky because uh
[133:44] uh you may have lots of bugs in the code
[133:47] you may have lots of bugs in the code and uh your network might actually work
[133:49] and uh your network might actually work just like ours worked
[133:51] just like ours worked but chances are is that if we had a more
[133:53] but chances are is that if we had a more complex problem then actually this bug
[133:55] complex problem then actually this bug would have made us not optimize the loss
[133:57] would have made us not optimize the loss very well and we were only able to get
[133:59] very well and we were only able to get away with it because
[134:01] away with it because the problem is very simple
[134:03] the problem is very simple so let's now bring everything together
[134:04] so let's now bring everything together and summarize what we learned
[134:06] and summarize what we learned what are neural nets neural nets are
[134:09] what are neural nets neural nets are these mathematical expressions
[134:11] these mathematical expressions fairly simple mathematical expressions
[134:13] fairly simple mathematical expressions in the case of multi-layer perceptron
[134:15] in the case of multi-layer perceptron that take
[134:16] that take input as the data and they take input
[134:19] input as the data and they take input the weights and the parameters of the
[134:20] the weights and the parameters of the neural net mathematical expression for
[134:22] neural net mathematical expression for the forward pass followed by a loss
[134:24] the forward pass followed by a loss function and the loss function tries to
[134:26] function and the loss function tries to measure the accuracy of the predictions
[134:29] measure the accuracy of the predictions and usually the loss will be low when
[134:31] and usually the loss will be low when your predictions are matching your
[134:32] your predictions are matching your targets or where the network is
[134:34] targets or where the network is basically behaving well so we we
[134:37] basically behaving well so we we manipulate the loss function so that
[134:38] manipulate the loss function so that when the loss is low the network is
[134:40] when the loss is low the network is doing what you want it to do on your
[134:42] doing what you want it to do on your problem
[134:44] problem and then we backward the loss
[134:46] and then we backward the loss use backpropagation to get the gradient
[134:48] use backpropagation to get the gradient and then we know how to tune all the
[134:50] and then we know how to tune all the parameters to decrease the loss locally
[134:52] parameters to decrease the loss locally but then we have to iterate that process
[134:54] but then we have to iterate that process many times in what's called the gradient
[134:55] many times in what's called the gradient descent
[134:56] descent so we simply follow the gradient
[134:58] so we simply follow the gradient information and that minimizes the loss
[135:01] information and that minimizes the loss and the loss is arranged so that when
[135:02] and the loss is arranged so that when the loss is minimized the network is
[135:04] the loss is minimized the network is doing what you want it to do
[135:06] doing what you want it to do and yeah so we just have a blob of
[135:09] and yeah so we just have a blob of neural stuff and we can make it do
[135:11] neural stuff and we can make it do arbitrary things and that's what gives
[135:13] arbitrary things and that's what gives neural nets their power um
[135:15] neural nets their power um it's you know this is a very tiny
[135:16] it's you know this is a very tiny network with 41 parameters
[135:19] network with 41 parameters but you can build significantly more
[135:20] but you can build significantly more complicated neural nets with billions
[135:24] complicated neural nets with billions at this point almost trillions of
[135:25] at this point almost trillions of parameters and it's a massive blob of
[135:28] parameters and it's a massive blob of neural tissue simulated neural tissue
[135:31] neural tissue simulated neural tissue roughly speaking
[135:32] roughly speaking and you can make it do extremely complex
[135:34] and you can make it do extremely complex problems and these neurons then have all
[135:37] problems and these neurons then have all kinds of very fascinating emergent
[135:39] kinds of very fascinating emergent properties
[135:40] properties in
[135:41] in when you try to make them do
[135:43] when you try to make them do significantly hard problems as in the
[135:45] significantly hard problems as in the case of gpt for example
[135:47] case of gpt for example we have massive amounts of text from the
[135:49] we have massive amounts of text from the internet and we're trying to get a
[135:51] internet and we're trying to get a neural net to predict to take like a few
[135:53] neural net to predict to take like a few words and try to predict the next word
[135:55] words and try to predict the next word in a sequence that's the learning
[135:56] in a sequence that's the learning problem
[135:57] problem and it turns out that when you train
[135:58] and it turns out that when you train this on all of internet the neural net
[136:00] this on all of internet the neural net actually has like really remarkable
[136:02] actually has like really remarkable emergent properties but that neural net
[136:04] emergent properties but that neural net would have hundreds of billions of
[136:05] would have hundreds of billions of parameters
[136:07] parameters but it works on fundamentally the exact
[136:09] but it works on fundamentally the exact same principles
[136:10] same principles the neural net of course will be a bit
[136:12] the neural net of course will be a bit more complex but otherwise the
[136:15] more complex but otherwise the value in the gradient is there
[136:17] value in the gradient is there and would be identical and the gradient
[136:19] and would be identical and the gradient descent would be there and would be
[136:21] descent would be there and would be basically identical but people usually
[136:23] basically identical but people usually use slightly different updates this is a
[136:25] use slightly different updates this is a very simple stochastic gradient descent
[136:27] very simple stochastic gradient descent update
[136:28] update um
[136:29] um and the loss function would not be mean
[136:30] and the loss function would not be mean squared error they would be using
[136:32] squared error they would be using something called the cross-entropy loss
[136:34] something called the cross-entropy loss for predicting the next token so there's
[136:36] for predicting the next token so there's a few more details but fundamentally the
[136:37] a few more details but fundamentally the neural network setup and neural network
[136:39] neural network setup and neural network training is identical and pervasive and
[136:42] training is identical and pervasive and now you understand intuitively
[136:44] now you understand intuitively how that works under the hood in the
[136:46] how that works under the hood in the beginning of this video i told you that
[136:47] beginning of this video i told you that by the end of it you would understand
[136:48] by the end of it you would understand everything in micrograd and then we'd
[136:50] everything in micrograd and then we'd slowly build it up let me briefly prove
[136:52] slowly build it up let me briefly prove that to you
[136:54] that to you so i'm going to step through all the
[136:55] so i'm going to step through all the code that is in micrograd as of today
[136:57] code that is in micrograd as of today actually potentially some of the code
[136:59] actually potentially some of the code will change by the time you watch this
[137:00] will change by the time you watch this video because i intend to continue
[137:01] video because i intend to continue developing micrograd
[137:03] developing micrograd but let's look at what we have so far at
[137:05] but let's look at what we have so far at least init.pi is empty when you go to
[137:07] least init.pi is empty when you go to engine.pi that has the value
[137:10] engine.pi that has the value everything here you should mostly
[137:11] everything here you should mostly recognize so we have the data.grad
[137:13] recognize so we have the data.grad attributes we have the backward function
[137:15] attributes we have the backward function uh we have the previous set of children
[137:17] uh we have the previous set of children and the operation that produced this
[137:19] and the operation that produced this value
[137:20] value we have addition multiplication and
[137:22] we have addition multiplication and raising to a scalar power
[137:25] raising to a scalar power we have the relu non-linearity which is
[137:27] we have the relu non-linearity which is slightly different type of nonlinearity
[137:28] slightly different type of nonlinearity than 10h that we used in this video
[137:30] than 10h that we used in this video both of them are non-linearities and
[137:32] both of them are non-linearities and notably 10h is not actually present in
[137:34] notably 10h is not actually present in micrograd as of right now but i intend
[137:37] micrograd as of right now but i intend to add it later
[137:38] to add it later with the backward which is identical and
[137:40] with the backward which is identical and then all of these other operations which
[137:42] then all of these other operations which are built up on top of operations here
[137:45] are built up on top of operations here so values should be very recognizable
[137:47] so values should be very recognizable except for the non-linearity used in
[137:48] except for the non-linearity used in this video
[137:50] this video um there's no massive difference between
[137:52] um there's no massive difference between relu and 10h and sigmoid and these other
[137:54] relu and 10h and sigmoid and these other non-linearities they're all roughly
[137:55] non-linearities they're all roughly equivalent and can be used in mlps so i
[137:58] equivalent and can be used in mlps so i use 10h because it's a bit smoother and
[138:00] use 10h because it's a bit smoother and because it's a little bit more
[138:01] because it's a little bit more complicated than relu and therefore it's
[138:03] complicated than relu and therefore it's stressed a little bit more the
[138:05] stressed a little bit more the local gradients and working with those
[138:07] local gradients and working with those derivatives which i thought would be
[138:09] derivatives which i thought would be useful
[138:10] useful and then that pi is the neural networks
[138:12] and then that pi is the neural networks library as i mentioned so you should
[138:14] library as i mentioned so you should recognize identical implementation of
[138:16] recognize identical implementation of neuron layer and mlp
[138:18] neuron layer and mlp notably or not so much
[138:20] notably or not so much we have a class module here there is a
[138:22] we have a class module here there is a parent class of all these modules i did
[138:24] parent class of all these modules i did that because there's an nn.module class
[138:27] that because there's an nn.module class in pytorch and so this exactly matches
[138:29] in pytorch and so this exactly matches that api and end.module and pytorch has
[138:31] that api and end.module and pytorch has also a zero grad which i've refactored
[138:33] also a zero grad which i've refactored out here
[138:36] so that's the end of micrograd really then there's a test
[138:39] then there's a test which you'll see
[138:41] which you'll see basically creates
[138:42] basically creates two chunks of code one in micrograd and
[138:45] two chunks of code one in micrograd and one in pi torch and we'll make sure that
[138:47] one in pi torch and we'll make sure that the forward and the backward pass agree
[138:49] the forward and the backward pass agree identically
[138:50] identically for a slightly less complicated
[138:51] for a slightly less complicated expression a slightly more complicated
[138:53] expression a slightly more complicated expression everything
[138:55] expression everything agrees so we agree with pytorch on all
[138:57] agrees so we agree with pytorch on all of these operations
[138:58] of these operations and finally there's a demo.ipymb here
[139:01] and finally there's a demo.ipymb here and it's a bit more complicated binary
[139:03] and it's a bit more complicated binary classification demo than the one i
[139:04] classification demo than the one i covered in this lecture so we only had a
[139:07] covered in this lecture so we only had a tiny data set of four examples um here
[139:09] tiny data set of four examples um here we have a bit more complicated example
[139:11] we have a bit more complicated example with lots of blue points and lots of red
[139:13] with lots of blue points and lots of red points and we're trying to again build a
[139:15] points and we're trying to again build a binary classifier to distinguish uh two
[139:18] binary classifier to distinguish uh two dimensional points as red or blue
[139:20] dimensional points as red or blue it's a bit more complicated mlp here
[139:22] it's a bit more complicated mlp here with it's a bigger mlp
[139:24] with it's a bigger mlp the loss is a bit more complicated
[139:26] the loss is a bit more complicated because
[139:27] because it supports batches
[139:29] it supports batches so because our dataset was so tiny we
[139:31] so because our dataset was so tiny we always did a forward pass on the entire
[139:32] always did a forward pass on the entire data set of four examples but when your
[139:35] data set of four examples but when your data set is like a million examples what
[139:37] data set is like a million examples what we usually do in practice is we chair we
[139:39] we usually do in practice is we chair we basically pick out some random subset we
[139:41] basically pick out some random subset we call that a batch and then we only
[139:43] call that a batch and then we only process the batch forward backward and
[139:45] process the batch forward backward and update so we don't have to forward the
[139:47] update so we don't have to forward the entire training set
[139:49] entire training set so this supports batching because
[139:51] so this supports batching because there's a lot more examples here
[139:53] there's a lot more examples here we do a forward pass the loss is
[139:55] we do a forward pass the loss is slightly more different this is a max
[139:57] slightly more different this is a max margin loss that i implement here
[140:00] margin loss that i implement here the one that we used was the mean
[140:01] the one that we used was the mean squared error loss because it's the
[140:03] squared error loss because it's the simplest one
[140:04] simplest one there's also the binary cross entropy
[140:06] there's also the binary cross entropy loss all of them can be used for binary
[140:08] loss all of them can be used for binary classification and don't make too much
[140:10] classification and don't make too much of a difference in the simple examples
[140:11] of a difference in the simple examples that we looked at so far
[140:13] that we looked at so far there's something called l2
[140:14] there's something called l2 regularization used here this has to do
[140:17] regularization used here this has to do with generalization of the neural net
[140:19] with generalization of the neural net and controls the overfitting in machine
[140:21] and controls the overfitting in machine learning setting but i did not cover
[140:23] learning setting but i did not cover these concepts and concepts in this
[140:24] these concepts and concepts in this video potentially later
[140:26] video potentially later and the training loop you should
[140:27] and the training loop you should recognize so forward backward with zero
[140:31] recognize so forward backward with zero grad
[140:32] grad and update and so on you'll notice that
[140:35] and update and so on you'll notice that in the update here the learning rate is
[140:36] in the update here the learning rate is scaled as a function of number of
[140:38] scaled as a function of number of iterations and it
[140:40] iterations and it shrinks
[140:41] shrinks and this is something called learning
[140:43] and this is something called learning rate decay so in the beginning you have
[140:44] rate decay so in the beginning you have a high learning rate and as the network
[140:47] a high learning rate and as the network sort of stabilizes near the end you
[140:49] sort of stabilizes near the end you bring down the learning rate to get some
[140:50] bring down the learning rate to get some of the fine details in the end
[140:53] of the fine details in the end and in the end we see the decision
[140:54] and in the end we see the decision surface of the neural net and we see
[140:56] surface of the neural net and we see that it learns to separate out the red
[140:58] that it learns to separate out the red and the blue area based on the data
[141:00] and the blue area based on the data points
[141:01] points so that's the slightly more complicated
[141:03] so that's the slightly more complicated example and then we'll demo that hyper
[141:05] example and then we'll demo that hyper ymb that you're free to go over
[141:07] ymb that you're free to go over but yeah as of today that is micrograd i
[141:10] but yeah as of today that is micrograd i also wanted to show you a little bit of
[141:11] also wanted to show you a little bit of real stuff so that you get to see how
[141:13] real stuff so that you get to see how this is actually implemented in
[141:14] this is actually implemented in production grade library like by torch
[141:16] production grade library like by torch uh so in particular i wanted to show i
[141:18] uh so in particular i wanted to show i wanted to find and show you the backward
[141:20] wanted to find and show you the backward pass for 10h in pytorch so here in
[141:23] pass for 10h in pytorch so here in micrograd we see that the backward
[141:25] micrograd we see that the backward password 10h is one minus t square
[141:28] password 10h is one minus t square where t is the output of the tanh of x
[141:33] times of that grad which is the chain rule so we're looking for something that
[141:36] rule so we're looking for something that looks like this
[141:38] looks like this now
[141:39] now i went to pytorch um which has an open
[141:42] i went to pytorch um which has an open source github codebase and uh i looked
[141:45] source github codebase and uh i looked through a lot of its code
[141:47] through a lot of its code and honestly i i i spent about 15
[141:49] and honestly i i i spent about 15 minutes and i couldn't find 10h
[141:51] minutes and i couldn't find 10h and that's because these libraries
[141:53] and that's because these libraries unfortunately they grow in size and
[141:55] unfortunately they grow in size and entropy and if you just search for 10h
[141:57] entropy and if you just search for 10h you get apparently 2 800 results and 400
[142:01] you get apparently 2 800 results and 400 and 406 files so i don't know what these
[142:04] and 406 files so i don't know what these files are doing honestly
[142:07] files are doing honestly and why there are so many mentions of
[142:09] and why there are so many mentions of 10h but unfortunately these libraries
[142:11] 10h but unfortunately these libraries are quite complex they're meant to be
[142:12] are quite complex they're meant to be used not really inspected um
[142:15] used not really inspected um eventually i did stumble on someone
[142:18] eventually i did stumble on someone who tries to change the 10 h backward
[142:21] who tries to change the 10 h backward code for some reason
[142:22] code for some reason and someone here pointed to the cpu
[142:24] and someone here pointed to the cpu kernel and the kuda kernel for 10 inch
[142:26] kernel and the kuda kernel for 10 inch backward
[142:27] backward so this so basically depends on if
[142:29] so this so basically depends on if you're using pi torch on a cpu device or
[142:31] you're using pi torch on a cpu device or on a gpu which these are different
[142:33] on a gpu which these are different devices and i haven't covered this but
[142:35] devices and i haven't covered this but this is the 10 h backwards kernel
[142:37] this is the 10 h backwards kernel for uh cpu
[142:40] for uh cpu and the reason it's so large is that
[142:43] and the reason it's so large is that number one this is like if you're using
[142:45] number one this is like if you're using a complex type which we haven't even
[142:46] a complex type which we haven't even talked about if you're using a specific
[142:48] talked about if you're using a specific data type of b-float 16 which we haven't
[142:50] data type of b-float 16 which we haven't talked about
[142:52] talked about and then if you're not then this is the
[142:54] and then if you're not then this is the kernel and deep here we see something
[142:57] kernel and deep here we see something that resembles our backward pass so they
[143:00] that resembles our backward pass so they have a times one minus
[143:02] have a times one minus b square uh so this b
[143:05] b square uh so this b b here must be the output of the 10h and
[143:07] b here must be the output of the 10h and this is the health.grad so here we found
[143:10] this is the health.grad so here we found it
[143:11] it uh deep inside
[143:14] uh deep inside pi torch from this location for some
[143:15] pi torch from this location for some reason inside binaryops kernel when 10h
[143:18] reason inside binaryops kernel when 10h is not actually a binary op
[143:21] is not actually a binary op and then this is the gpu kernel
[143:25] we're not complex we're
[143:27] we're here and here we go with one line of
[143:29] here and here we go with one line of code
[143:30] code so we did find it but basically
[143:33] so we did find it but basically unfortunately these codepieces are very
[143:34] unfortunately these codepieces are very large and
[143:36] large and micrograd is very very simple but if you
[143:38] micrograd is very very simple but if you actually want to use real stuff uh
[143:40] actually want to use real stuff uh finding the code for it you'll actually
[143:41] finding the code for it you'll actually find that difficult
[143:43] find that difficult i also wanted to show you a little
[143:45] i also wanted to show you a little example here where pytorch is showing
[143:47] example here where pytorch is showing you how can you can register a new type
[143:49] you how can you can register a new type of function that you want to add to
[143:51] of function that you want to add to pytorch as a lego building block
[143:53] pytorch as a lego building block so here if you want to for example add a
[143:55] so here if you want to for example add a gender polynomial 3
[143:59] gender polynomial 3 here's how you could do it you will
[144:00] here's how you could do it you will register it as a class that
[144:03] register it as a class that subclasses storage.org that function
[144:06] subclasses storage.org that function and then you have to tell pytorch how to
[144:07] and then you have to tell pytorch how to forward your new function
[144:10] forward your new function and how to backward through it
[144:12] and how to backward through it so as long as you can do the forward
[144:14] so as long as you can do the forward pass of this little function piece that
[144:15] pass of this little function piece that you want to add and as long as you know
[144:17] you want to add and as long as you know the the local derivative the local
[144:19] the the local derivative the local gradients which are implemented in the
[144:20] gradients which are implemented in the backward pi torch will be able to back
[144:22] backward pi torch will be able to back propagate through your function and then
[144:24] propagate through your function and then you can use this as a lego block in a
[144:26] you can use this as a lego block in a larger lego castle of all the different
[144:28] larger lego castle of all the different lego blocks that pytorch already has
[144:31] lego blocks that pytorch already has and so that's the only thing you have to
[144:32] and so that's the only thing you have to tell pytorch and everything would just
[144:33] tell pytorch and everything would just work and you can register new types of
[144:35] work and you can register new types of functions
[144:36] functions in this way following this example
[144:38] in this way following this example and that is everything that i wanted to
[144:40] and that is everything that i wanted to cover in this lecture
[144:41] cover in this lecture so i hope you enjoyed building out
[144:42] so i hope you enjoyed building out micrograd with me i hope you find it
[144:44] micrograd with me i hope you find it interesting insightful
[144:46] interesting insightful and
[144:47] and yeah i will post a lot of the links
[144:50] yeah i will post a lot of the links that are related to this video in the
[144:51] that are related to this video in the video description below i will also
[144:53] video description below i will also probably post a link to a discussion
[144:55] probably post a link to a discussion forum
[144:56] forum or discussion group where you can ask
[144:58] or discussion group where you can ask questions related to this video and then
[145:00] questions related to this video and then i can answer or someone else can answer
[145:02] i can answer or someone else can answer your questions and i may also do a
[145:04] your questions and i may also do a follow-up video that answers some of the
[145:06] follow-up video that answers some of the most common questions
[145:08] most common questions but for now that's it i hope you enjoyed
[145:10] but for now that's it i hope you enjoyed it if you did then please like and
[145:11] it if you did then please like and subscribe so that youtube knows to
[145:13] subscribe so that youtube knows to feature this video to more people
[145:15] feature this video to more people and that's it for now i'll see you later
[145:22] now here's the problem we know
[145:25] we know dl by
[145:28] dl by wait what is the problem
[145:31] and that's everything i wanted to cover in this lecture
[145:34] in this lecture so i hope
[145:35] so i hope you enjoyed us building up microcraft
[145:38] you enjoyed us building up microcraft micro crab
[145:42] okay now let's do the exact same thing for multiply because we can't do
[145:44] for multiply because we can't do something like a times two
[145:47] something like a times two oops
[145:50] i know what happened there
