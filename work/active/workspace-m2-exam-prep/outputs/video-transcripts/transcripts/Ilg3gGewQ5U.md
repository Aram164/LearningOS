---
video_id: Ilg3gGewQ5U
url: https://www.youtube.com/watch?v=Ilg3gGewQ5U
title: Backpropagation, intuitively | Deep Learning Chapter 3
channel: 3Blue1Brown
duration: 12:47
language: en
unit: L15
status: OK
---

[00:04] Here, we tackle backpropagation, the core algorithm behind how neural networks learn.
[00:09] After a quick recap for where we are, the first thing I'll do is an intuitive walkthrough
[00:13] for what the algorithm is actually doing, without any reference to the formulas.
[00:17] Then, for those of you who do want to dive into the math,
[00:20] the next video goes into the calculus underlying all this.
[00:23] If you watched the last two videos, or if you're just jumping in with the appropriate
[00:27] background, you know what a neural network is, and how it feeds forward information.
[00:31] Here, we're doing the classic example of recognizing handwritten digits whose pixel
[00:36] values get fed into the first layer of the network with 784 neurons,
[00:39] and I've been showing a network with two hidden layers having just 16 neurons each,
[00:43] and an output layer of 10 neurons, indicating which digit the network is choosing
[00:48] as its answer.
[00:50] I'm also expecting you to understand gradient descent,
[00:53] as described in the last video, and how what we mean by learning is
[00:56] that we want to find which weights and biases minimize a certain cost function.
[01:02] As a quick reminder, for the cost of a single training example,
[01:05] you take the output the network gives, along with the output you wanted it to give,
[01:10] and add up the squares of the differences between each component.
[01:15] Doing this for all of your tens of thousands of training examples and
[01:18] averaging the results, this gives you the total cost of the network.
[01:22] And as if that's not enough to think about, as described in the last video,
[01:26] the thing that we're looking for is the negative gradient of this cost function,
[01:30] which tells you how you need to change all of the weights and biases,
[01:34] all of these connections, so as to most efficiently decrease the cost.
[01:43] Backpropagation, the topic of this video, is an
[01:45] algorithm for computing that crazy complicated gradient.
[01:49] And the one idea from the last video that I really want you to hold firmly
[01:52] in your mind right now is that because thinking of the gradient vector
[01:56] as a direction in 13,000 dimensions is, to put it lightly,
[01:59] beyond the scope of our imaginations, there's another way you can think about it.
[02:04] The magnitude of each component here is telling you how
[02:07] sensitive the cost function is to each weight and bias.
[02:11] For example, let's say you go through the process I'm about to describe,
[02:15] and you compute the negative gradient, and the component associated with the weight on
[02:20] this edge here comes out to be 3.2, while the component associated with this edge here
[02:25] comes out as 0.1.
[02:26] The way you would interpret that is that the cost of the function is 32 times more
[02:30] sensitive to changes in that first weight, so if you were to wiggle that value
[02:34] just a little bit, it's going to cause some change to the cost,
[02:38] and that change is 32 times greater than what the same wiggle to that second
[02:42] weight would give.
[02:48] Personally, when I was first learning about backpropagation,
[02:51] I think the most confusing aspect was just the notation and the index chasing of it all.
[02:56] But once you unwrap what each part of this algorithm is really doing,
[02:59] each individual effect it's having is actually pretty intuitive,
[03:02] it's just that there's a lot of little adjustments getting layered on top of each other.
[03:07] So I'm going to start things off here with a complete disregard for the notation,
[03:11] and just step through the effects each training example has on the weights and biases.
[03:17] Because the cost function involves averaging a certain cost per example over all
[03:21] the tens of thousands of training examples, the way we adjust the weights and
[03:26] biases for a single gradient descent step also depends on every single example.
[03:31] Or rather, in principle it should, but for computational efficiency we'll do a little
[03:35] trick later to keep you from needing to hit every single example for every step.
[03:39] In other cases, right now, all we're going to do is focus
[03:42] our attention on one single example, this image of a 2.
[03:46] What effect should this one training example have
[03:49] on how the weights and biases get adjusted?
[03:52] Let's say we're at a point where the network is not well trained yet,
[03:56] so the activations in the output are going to look pretty random,
[03:59] maybe something like 0.5, 0.8, 0.2, on and on.
[04:02] We can't directly change those activations, we
[04:04] only have influence on the weights and biases.
[04:07] But it's helpful to keep track of which adjustments
[04:09] we wish should take place to that output layer.
[04:13] And since we want it to classify the image as a 2,
[04:16] we want that third value to get nudged up while all the others get nudged down.
[04:22] Moreover, the sizes of these nudges should be proportional
[04:25] to how far away each current value is from its target value.
[04:30] For example, the increase to that number 2 neuron's activation
[04:33] is in a sense more important than the decrease to the number 8 neuron,
[04:37] which is already pretty close to where it should be.
[04:42] So zooming in further, let's focus just on this one neuron,
[04:44] the one whose activation we wish to increase.
[04:48] Remember, that activation is defined as a certain weighted sum of all the
[04:52] activations in the previous layer, plus a bias,
[04:55] which is all then plugged into something like the sigmoid squishification function,
[05:00] or a ReLU.
[05:01] So there are three different avenues that can team
[05:04] up together to help increase that activation.
[05:07] You can increase the bias, you can increase the weights,
[05:10] and you can change the activations from the previous layer.
[05:14] Focusing on how the weights should be adjusted,
[05:17] notice how the weights actually have differing levels of influence.
[05:21] The connections with the brightest neurons from the preceding layer have the
[05:25] biggest effect since those weights are multiplied by larger activation values.
[05:31] So if you were to increase one of those weights,
[05:33] it actually has a stronger influence on the ultimate cost function than increasing
[05:38] the weights of connections with dimmer neurons,
[05:40] at least as far as this one training example is concerned.
[05:44] Remember, when we talk about gradient descent,
[05:46] we don't just care about whether each component should get nudged up or down,
[05:50] we care about which ones give you the most bang for your buck.
[05:55] This, by the way, is at least somewhat reminiscent of a theory in
[05:58] neuroscience for how biological networks of neurons learn, Hebbian theory,
[06:02] often summed up in the phrase, neurons that fire together wire together.
[06:07] Here, the biggest increases to weights, the biggest strengthening of connections,
[06:11] happens between neurons which are the most active,
[06:14] and the ones which we wish to become more active.
[06:17] In a sense, the neurons that are firing while seeing a 2 get
[06:21] more strongly linked to those firing when thinking about a 2.
[06:25] To be clear, I'm not in a position to make statements one way or another about
[06:29] whether artificial networks of neurons behave anything like biological brains,
[06:33] and this fires together wire together idea comes with a couple meaningful asterisks,
[06:37] but taken as a very loose analogy, I find it interesting to note.
[06:41] Anyway, the third way we can help increase this neuron's activation
[06:45] is by changing all the activations in the previous layer.
[06:49] Namely, if everything connected to that digit 2 neuron with a positive
[06:53] weight got brighter, and if everything connected with a negative weight got dimmer,
[06:57] then that digit 2 neuron would become more active.
[07:02] And similar to the weight changes, you're going to get the most bang for your buck
[07:06] by seeking changes that are proportional to the size of the corresponding weights.
[07:12] Now of course, we cannot directly influence those activations,
[07:15] we only have control over the weights and biases.
[07:17] But just as with the last layer, it's helpful to
[07:20] keep a note of what those desired changes are.
[07:24] But keep in mind, zooming out one step here, this
[07:26] is only what that digit 2 output neuron wants.
[07:29] Remember, we also want all the other neurons in the last layer to become less active,
[07:33] and each of those other output neurons has its own thoughts about
[07:37] what should happen to that second to last layer.
[07:42] So, the desire of this digit 2 neuron is added together with the desires
[07:47] of all the other output neurons for what should happen to this second to last layer,
[07:52] again in proportion to the corresponding weights,
[07:56] and in proportion to how much each of those neurons needs to change.
[08:01] This right here is where the idea of propagating backwards comes in.
[08:05] By adding together all these desired effects, you basically get a
[08:09] list of nudges that you want to happen to this second to last layer.
[08:14] And once you have those, you can recursively apply the same process to the
[08:17] relevant weights and biases that determine those values,
[08:20] repeating the same process I just walked through and moving backwards
[08:24] through the network.
[08:28] And zooming out a bit further, remember that this is all just how a single
[08:33] training example wishes to nudge each one of those weights and biases.
[08:37] If we only listened to what that 2 wanted, the network would
[08:40] ultimately be incentivized just to classify all images as a 2.
[08:44] So what you do is go through this same backprop routine for every other training example,
[08:49] recording how each of them would like to change the weights and biases,
[08:53] and average together those desired changes.
[09:01] This collection here of the averaged nudges to each weight and bias is,
[09:05] loosely speaking, the negative gradient of the cost function referenced
[09:10] in the last video, or at least something proportional to it.
[09:14] I say loosely speaking only because I have yet to get quantitatively precise
[09:18] about those nudges, but if you understood every change I just referenced,
[09:22] why some are proportionally bigger than others,
[09:24] and how they all need to be added together, you understand the mechanics for
[09:28] what backpropagation is actually doing.
[09:33] By the way, in practice, it takes computers an extremely long time to add
[09:38] up the influence of every training example every gradient descent step.
[09:43] So here's what's commonly done instead.
[09:45] You randomly shuffle your training data and then divide it into a whole
[09:48] bunch of mini-batches, let's say each one having 100 training examples.
[09:52] Then you compute a step according to the mini-batch.
[09:56] It's not going to be the actual gradient of the cost function,
[10:00] which depends on all of the training data, not this tiny subset,
[10:03] so it's not the most efficient step downhill,
[10:05] but each mini-batch does give you a pretty good approximation, and more importantly,
[10:09] it gives you a significant computational speedup.
[10:12] If you were to plot the trajectory of your network under the relevant cost surface,
[10:17] it would be a little more like a drunk man stumbling aimlessly down a hill but taking
[10:21] quick steps, rather than a carefully calculating man determining the exact downhill
[10:25] direction of each step before taking a very slow and careful step in that direction.
[10:31] This technique is referred to as stochastic gradient descent.
[10:35] There's a lot going on here, so let's just sum it up for ourselves, shall we?
[10:40] Backpropagation is the algorithm for determining how a single training
[10:44] example would like to nudge the weights and biases,
[10:47] not just in terms of whether they should go up or down,
[10:50] but in terms of what relative proportions to those changes cause the
[10:53] most rapid decrease to the cost.
[10:56] A true gradient descent step would involve doing this for all your tens of
[11:00] thousands of training examples and averaging the desired changes you get.
[11:04] But that's computationally slow, so instead you randomly subdivide the
[11:08] data into mini-batches and compute each step with respect to a mini-batch.
[11:14] Repeatedly going through all of the mini-batches and making these adjustments,
[11:17] you will converge towards a local minimum of the cost function,
[11:21] which is to say your network will end up doing a really good job on the training
[11:25] examples.
[11:27] So with all of that said, every line of code that would go into implementing backprop
[11:32] actually corresponds with something you have now seen, at least in informal terms.
[11:37] But sometimes knowing what the math does is only half the battle,
[11:40] and just representing the damn thing is where it gets all muddled and confusing.
[11:44] So for those of you who do want to go deeper, the next video goes through the same
[11:48] ideas that were just presented here, but in terms of the underlying calculus,
[11:52] which should hopefully make it a little more familiar as you see the topic in other
[11:55] resources.
[11:57] Before that, one thing worth emphasizing is that for this algorithm to work,
[12:00] and this goes for all sorts of machine learning beyond just neural networks,
[12:04] you need a lot of training data.
[12:06] In our case, one thing that makes handwritten digits such a nice example is that there
[12:10] exists the MNIST database, with so many examples that have been labeled by humans.
[12:15] So a common challenge that those of you working in machine learning will be familiar with
[12:19] is just getting the labeled training data you actually need,
[12:21] whether that's having people label tens of thousands of images,
[12:24] or whatever other data type you might be dealing with.
