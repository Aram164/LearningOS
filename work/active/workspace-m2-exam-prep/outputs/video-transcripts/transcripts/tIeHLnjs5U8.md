---
video_id: tIeHLnjs5U8
url: https://www.youtube.com/watch?v=tIeHLnjs5U8
title: Backpropagation calculus | Deep Learning Chapter 4
channel: 3Blue1Brown
duration: 10:17
language: en
unit: L15
status: OK
---

[00:00] [Submit subtitle corrections at criblate.com]
[00:04] The hard assumption here is that you've watched part 3,
[00:06] giving an intuitive walkthrough of the backpropagation algorithm.
[00:11] Here we get a little more formal and dive into the relevant calculus.
[00:14] It's normal for this to be at least a little confusing,
[00:17] so the mantra to regularly pause and ponder certainly applies as much here
[00:20] as anywhere else.
[00:21] Our main goal is to show how people in machine learning commonly think about
[00:25] the chain rule from calculus in the context of networks,
[00:28] which has a different feel from how most introductory calculus courses
[00:32] approach the subject.
[00:34] For those of you uncomfortable with the relevant calculus,
[00:36] I do have a whole series on the topic.
[00:39] Let's start off with an extremely simple network,
[00:43] one where each layer has a single neuron in it.
[00:46] This network is determined by three weights and three biases,
[00:49] and our goal is to understand how sensitive the cost function is to these variables.
[00:55] That way, we know which adjustments to those terms will
[00:58] cause the most efficient decrease to the cost function.
[01:01] And we're just going to focus on the connection between the last two neurons.
[01:05] Let's label the activation of that last neuron with a superscript L,
[01:10] indicating which layer it's in, so the activation of the previous neuron is a^(L-1).
[01:16] These are not exponents, they're just a way of indexing what we're talking about,
[01:20] since I want to save subscripts for different indices later on.
[01:23] Let's say that the value we want this last activation to be for
[01:27] a given training example is y, for example, y might be 0 or 1.
[01:32] So the cost of this network for a single training example is a^(L - y) squared.
[01:40] We'll denote the cost of that one training example as C0.
[01:45] As a reminder, this last activation is determined by a weight,
[01:49] which I'm going to call w(L), times the previous neuron's activation plus some bias,
[01:55] which I'll call b(L).
[01:57] And then you pump that through some special nonlinear function like the sigmoid or ReLU.
[02:01] It's actually going to make things easier for us if we give a special name to
[02:05] this weighted sum, like z, with the same superscript as the relevant activations.
[02:10] This is a lot of terms, and a way you might conceptualize it is that the weight,
[02:15] previous action and the bias all together are used to compute z,
[02:19] which in turn lets us compute a, which finally, along with a constant y,
[02:23] lets us compute the cost.
[02:27] And of course a(L-1) is influenced by its own weight and bias and such...
[02:31] but we're not going to focus on that right now.
[02:35] All of these are just numbers, right?
[02:38] And it can be nice to think of each one as having its own little number line.
[02:41] Our first goal is to understand how sensitive the
[02:45] cost function is to small changes in our weight w(L).
[02:49] Or phrased differently, what is the derivative of C with respect to w(L)?
[02:55] When you see this del w term, think of it as meaning some tiny nudge to W,
[03:00] like a change by 0.01, and think of this del C term as meaning
[03:04] whatever the resulting nudge to the cost is.
[03:08] What we want is their ratio.
[03:11] Conceptually, this tiny nudge to w(L) causes some nudge to z(L),
[03:15] which in turn causes some nudge to a(L), which directly influences the cost.
[03:23] So we break things up by first looking at the ratio of a tiny change to z(L) to
[03:28] this tiny change w(L), that is, the derivative of z(L) with respect to w(L).
[03:33] Likewise, you then consider the ratio of the change to a(L) to
[03:36] the tiny change in z(L) that caused it, as well as the ratio
[03:40] between the final nudge to C and this intermediate nudge to a(L).
[03:45] This right here is the chain rule, where multiplying together these
[03:50] three ratios gives us the sensitivity of C to small changes in w(L).
[03:56] So on screen right now, there's a lot of symbols,
[03:59] and take a moment to make sure it's clear what they all are,
[04:02] because now we're going to compute the relevant derivatives.
[04:07] The derivative of C with respect to a(L) works out to be 2(a(L)-y).
[04:13] Notice this means its size is proportional to the difference between the network's
[04:18] output and the thing we want it to be, so if that output was very different,
[04:22] even slight changes stand to have a big impact on the final cost function.
[04:27] The derivative of a(L) with respect to z(L) is just the derivative
[04:31] of our sigmoid function, or whatever nonlinearity you choose to use.
[04:37] And the derivative of z(L) with respect to w(L)... In this case comes out to be a(L-1).
[04:45] Now I don't know about you, but I think it's easy to get stuck head down in the
[04:49] formulas without taking a moment to sit back and remind yourself of what they all mean.
[04:53] In the case of this last derivative, the amount that the small nudge to the
[04:58] weight influenced the last layer depends on how strong the previous neuron is.
[05:03] Remember, this is where the neurons-that-fire-together-wire-together idea comes in.
[05:09] And all of this is the derivative with respect to w(L)
[05:12] only of the cost for a specific single training example.
[05:16] Since the full cost function involves averaging together all
[05:19] those costs across many different training examples,
[05:22] its derivative requires averaging this expression over all training examples.
[05:28] And of course, that is just one component of the gradient vector,
[05:31] which itself is built up from the partial derivatives of the
[05:35] cost function with respect to all those weights and biases.
[05:40] But even though that's just one of the many partial derivatives we need,
[05:43] it's more than 50% of the work.
[05:46] The sensitivity to the bias, for example, is almost identical.
[05:50] We just need to change out this del z del w term for a del z del b.
[05:58] And if you look at the relevant formula, that derivative comes out to be 1.
[06:06] Also, and this is where the idea of propagating backwards comes in,
[06:10] you can see how sensitive this cost function is to the activation of the previous layer.
[06:15] Namely, this initial derivative in the chain rule expression,
[06:19] the sensitivity of z to the previous activation, comes out to be the weight w(L).
[06:26] And again, even though we're not going to be able to directly influence
[06:30] that previous layer activation, it's helpful to keep track of,
[06:33] because now we can just keep iterating this same chain rule idea backwards
[06:37] to see how sensitive the cost function is to previous weights and previous biases.
[06:43] And you might think this is an overly simple example, since all layers have one neuron,
[06:47] and things are going to get exponentially more complicated for a real network.
[06:51] But honestly, not that much changes when we give the layers multiple neurons,
[06:55] really it's just a few more indices to keep track of.
[06:59] Rather than the activation of a given layer simply being a(L),
[07:02] it's also going to have a subscript indicating which neuron of that layer it is.
[07:07] Let's use the letter k to index the layer L-1, and j to index the layer L.
[07:15] For the cost, again we look at what the desired output is,
[07:18] but this time we add up the squares of the differences between these last layer
[07:23] activations and the desired output.
[07:26] That is, you take a sum over a(L)j minus yj squared.
[07:33] Since there's a lot more weights, each one has to have a couple more
[07:37] indices to keep track of where it is, so let's call the weight of
[07:41] the edge connecting this kth neuron to the jth neuron, w(L)_jk.
[07:45] Those indices might feel a little backwards at first,
[07:48] but it lines up with how you'd index the weight matrix I talked about in
[07:52] the part 1 video.
[07:53] Just as before, it's still nice to give a name to the relevant weighted sum,
[07:57] like z, so that the activation of the last layer is just your special function,
[08:02] like the sigmoid, applied to z.
[08:04] You can see what I mean, where all of these are essentially the same equations we had
[08:08] before in the one-neuron-per-layer case, it's just that it looks a little more
[08:13] complicated.
[08:15] And indeed, the chain-ruled derivative expression describing how
[08:19] sensitive the cost is to a specific weight looks essentially the same.
[08:23] I'll leave it to you to pause and think about each of those terms if you want.
[08:28] What does change here, though, is the derivative of the cost
[08:32] with respect to one of the activations in the layer L-1.
[08:37] In this case, the difference is that the neuron influences
[08:40] the cost function through multiple different paths.
[08:44] That is, on the one hand, it influences a(L)0, which plays a role in the cost function,
[08:50] but it also has an influence on a(L)1, which also plays a role in the cost function,
[08:55] and you have to add those up.
[08:59] And that, well, that's pretty much it.
[09:03] Once you know how sensitive the cost function is to the
[09:06] activations in this second-to-last layer, you can just repeat
[09:09] the process for all the weights and biases feeding into that layer.
[09:13] So pat yourself on the back!
[09:15] If all of this makes sense, you have now looked deep into the heart of backpropagation,
[09:20] the workhorse behind how neural networks learn.
[09:23] These chain rule expressions give you the derivatives that determine each component in
[09:28] the gradient that helps minimize the cost of the network by repeatedly stepping downhill.
[09:34] If you sit back and think about all that, this is a lot of layers of complexity to
[09:38] wrap your mind around, so don't worry if it takes time for your mind to digest it all.
