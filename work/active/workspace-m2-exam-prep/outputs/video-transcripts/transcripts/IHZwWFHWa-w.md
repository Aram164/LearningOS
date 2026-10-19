---
video_id: IHZwWFHWa-w
url: https://www.youtube.com/watch?v=IHZwWFHWa-w
title: Gradient descent, how neural networks learn | Deep Learning Chapter 2
channel: 3Blue1Brown
duration: 20:33
language: en
unit: L15
status: OK
---

[00:04] Last video I laid out the structure of a neural network.
[00:07] I'll give a quick recap here so that it's fresh in our minds,
[00:10] and then I have two main goals for this video.
[00:13] The first is to introduce the idea of gradient descent,
[00:15] which underlies not only how neural networks learn,
[00:18] but how a lot of other machine learning works as well.
[00:21] Then after that we'll dig in a little more into how this particular network performs,
[00:25] and what those hidden layers of neurons end up looking for.
[00:28] As a reminder, our goal here is the classic example of handwritten digit recognition,
[00:34] the hello world of neural networks.
[00:37] These digits are rendered on a 28x28 pixel grid,
[00:40] each pixel with some grayscale value between 0 and 1.
[00:43] Those are what determine the activations of 784 neurons in the input layer of the network.
[00:51] And then the activation for each neuron in the following layers is based on a weighted
[00:55] sum of all the activations in the previous layer, plus some special number called a bias.
[01:02] Then you compose that sum with some other function,
[01:04] like the sigmoid squishification, or a relu, the way I walked through last video.
[01:09] In total, given the somewhat arbitrary choice of two hidden layers with 16 neurons each,
[01:15] the network has about 13,000 weights and biases that we can adjust,
[01:19] and it's these values that determine what exactly the network actually does.
[01:24] Then what we mean when we say that this network classifies a given digit is that
[01:29] the brightest of those 10 neurons in the final layer corresponds to that digit.
[01:34] And remember, the motivation we had in mind here for the layered structure
[01:37] was that maybe the second layer could pick up on the edges,
[01:41] and the third layer might pick up on patterns like loops and lines,
[01:44] and the last one could just piece together those patterns to recognize digits.
[01:49] So here, we learn how the network learns.
[01:52] What we want is an algorithm where you can show this network a whole bunch of
[01:56] training data, which comes in the form of a bunch of different images of handwritten
[02:01] digits, along with labels for what they're supposed to be,
[02:04] and it'll adjust those 13,000 weights and biases so as to improve its performance
[02:08] on the training data.
[02:10] Hopefully, this layered structure will mean that what it
[02:13] learns generalizes to images beyond that training data.
[02:17] The way we test that is that after you train the network,
[02:20] you show it more labeled data that it's never seen before,
[02:23] and you see how accurately it classifies those new images.
[02:31] Fortunately for us, and what makes this such a common example to start with,
[02:34] is that the good people behind the MNIST database have put together a collection of tens
[02:39] of thousands of handwritten digit images, each one labeled with the numbers they're
[02:43] supposed to be.
[02:44] And as provocative as it is to describe a machine as learning,
[02:48] once you see how it works, it feels a lot less like some crazy sci-fi premise,
[02:53] and a lot more like a calculus exercise.
[02:56] I mean, basically it comes down to finding the minimum of a certain function.
[03:01] Remember, conceptually, we're thinking of each neuron as being connected to all
[03:06] the neurons in the previous layer, and the weights in the weighted sum defining
[03:10] its activation are kind of like the strengths of those connections,
[03:14] and the bias is some indication of whether that neuron tends to be active or inactive.
[03:19] And to start things off, we're just going to initialize
[03:22] all of those weights and biases totally randomly.
[03:24] Needless to say, this network is going to perform pretty horribly on
[03:27] a given training example, since it's just doing something random.
[03:31] For example, you feed in this image of a 3, and the output layer just looks like a mess.
[03:36] So what you do is define a cost function, a way of telling the computer,
[03:41] no, bad computer, that output should have activations which are 0 for most neurons,
[03:47] but 1 for this neuron, what you gave me is utter trash.
[03:51] To say that a little more mathematically, you add up the squares of the differences
[03:56] between each of those trash output activations and the value you want them to have,
[04:01] and this is what we'll call the cost of a single training example.
[04:05] Notice this sum is small when the network confidently classifies the image correctly,
[04:11] but it's large when the network seems like it doesn't know what it's doing.
[04:18] So then what you do is consider the average cost over all of
[04:22] the tens of thousands of training examples at your disposal.
[04:27] This average cost is our measure for how lousy the network is,
[04:30] and how bad the computer should feel.
[04:33] And that's a complicated thing.
[04:35] Remember how the network itself was basically a function,
[04:38] one that takes in 784 numbers as inputs, the pixel values,
[04:42] and spits out 10 numbers as its output, and in a sense it's parameterized
[04:46] by all these weights and biases?
[04:49] Well the cost function is a layer of complexity on top of that.
[04:53] It takes as its input those 13,000 or so weights and biases,
[04:56] and spits out a single number describing how bad those weights and biases are,
[05:01] and the way it's defined depends on the network's behavior over all the tens of
[05:06] thousands of pieces of training data.
[05:09] That's a lot to think about.
[05:12] But just telling the computer what a crappy job it's doing isn't very helpful.
[05:16] You want to tell it how to change those weights and biases so that it gets better.
[05:20] To make it easier, rather than struggling to imagine a function with 13,000 inputs,
[05:25] just imagine a simple function that has one number as an input and one number as an
[05:30] output.
[05:31] How do you find an input that minimizes the value of this function?
[05:36] Calculus students will know that you can sometimes figure out that minimum explicitly,
[05:41] but that's not always feasible for really complicated functions,
[05:44] certainly not in the 13,000 input version of this situation for our crazy complicated
[05:49] neural network cost function.
[05:51] A more flexible tactic is to start at any input,
[05:54] and figure out which direction you should step to make that output lower.
[06:00] Specifically, if you can figure out the slope of the function where you are,
[06:04] then shift to the left if that slope is positive,
[06:06] and shift the input to the right if that slope is negative.
[06:11] If you do this repeatedly, at each point checking the new slope and taking the
[06:15] appropriate step, you're going to approach some local minimum of the function.
[06:20] The image you might have in mind here is a ball rolling down a hill.
[06:24] Notice, even for this really simplified single input function,
[06:27] there are many possible valleys that you might land in,
[06:30] depending on which random input you start at,
[06:33] and there's no guarantee that the local minimum you land in is going to
[06:36] be the smallest possible value of the cost function.
[06:40] That will carry over to our neural network case as well.
[06:43] And I also want you to notice how if you make your step sizes proportional to the slope,
[06:47] then when the slope is flattening out towards the minimum,
[06:50] your steps get smaller and smaller, and that kind of helps you from overshooting.
[06:55] Bumping up the complexity a bit, imagine instead
[06:58] a function with two inputs and one output.
[07:01] You might think of the input space as the xy-plane,
[07:04] and the cost function as being graphed as a surface above it.
[07:08] Now instead of asking about the slope of the function,
[07:11] you have to ask which direction you should step in this input
[07:15] space so as to decrease the output of the function most quickly.
[07:19] In other words, what's the downhill direction?
[07:22] Again, it's helpful to think of a ball rolling down that hill.
[07:26] Those of you familiar with multivariable calculus will know that the
[07:30] gradient of a function gives you the direction of steepest ascent,
[07:34] which direction should you step to increase the function most quickly.
[07:39] Naturally enough, taking the negative of that gradient gives you
[07:42] the direction to step that decreases the function most quickly.
[07:47] Even more than that, the length of this gradient vector is
[07:50] an indication for just how steep that steepest slope is.
[07:54] If you're unfamiliar with multivariable calculus and want to learn more,
[07:57] check out some of the work I did for Khan Academy on the topic.
[08:00] Honestly though, all that matters for you and me right now is that
[08:04] in principle there exists a way to compute this vector,
[08:07] this vector that tells you what the downhill direction is and how steep it is.
[08:12] You'll be okay if that's all you know and you're not rock solid on the details.
[08:17] Cause If you can get that, the algorithm for minimizing the function is to compute this
[08:22] gradient direction, then take a small step downhill, and repeat that over and over.
[08:27] It's the same basic idea for a function that has 13,000 inputs instead of 2 inputs.
[08:33] Imagine organizing all 13,000 weights and biases
[08:36] of our network into a giant column vector.
[08:40] The negative gradient of the cost function is just a vector,
[08:43] it's some direction inside this insanely huge input space that tells you which
[08:48] nudges to all of those numbers is going to cause the most rapid decrease to
[08:53] the cost function.
[08:55] And of course, with our specially designed cost function,
[08:58] changing the weights and biases to decrease it means making the
[09:02] output of the network on each piece of training data look less like
[09:06] a random array of 10 values, and more like an actual decision we want it to make.
[09:11] It's important to remember, this cost function involves an average over all of the
[09:15] training data, so if you minimize it, it means it's a better performance on all of those
[09:20] samples.
[09:23] The algorithm for computing this gradient efficiently,
[09:26] which is effectively the heart of how a neural network learns,
[09:29] is called backpropagation, and it's what I'm going to be talking about next video.
[09:34] There, I really want to take the time to walk through what exactly happens to
[09:38] each weight and bias for a given piece of training data,
[09:41] trying to give an intuitive feel for what's happening beyond the pile of relevant
[09:45] calculus and formulas.
[09:47] Right here, right now, the main thing I want you to know,
[09:50] independent of implementation details, is that what we mean when we
[09:54] talk about a network learning is that it's just minimizing a cost function.
[09:59] And notice, one consequence of that is that it's important for this cost function to have
[10:03] a nice smooth output, so that we can find a local minimum by taking little steps
[10:07] downhill.
[10:09] This is why, by the way, artificial neurons have continuously ranging activations,
[10:13] rather than simply being active or inactive in a binary way,
[10:17] the way biological neurons are.
[10:20] This process of repeatedly nudging an input of a function by some
[10:23] multiple of the negative gradient is called gradient descent.
[10:27] It's a way to converge towards some local minimum of a cost function,
[10:30] basically a valley in this graph.
[10:33] I'm still showing the picture of a function with two inputs, of course,
[10:36] because nudges in a 13,000 dimensional input space are a little hard to
[10:40] wrap your mind around, but there is a nice non-spatial way to think about this.
[10:45] Each component of the negative gradient tells us two things.
[10:49] The sign, of course, tells us whether the corresponding
[10:51] component of the input vector should be nudged up or down.
[10:55] But importantly, the relative magnitudes of all these
[10:59] components kind of tells you which changes matter more.
[11:05] You see, in our network, an adjustment to one of the weights might have a much
[11:09] greater impact on the cost function than the adjustment to some other weight.
[11:14] Some of these connections just matter more for our training data.
[11:19] So a way you can think about this gradient vector of our mind-warpingly massive
[11:23] cost function is that it encodes the relative importance of each weight and bias,
[11:28] that is, which of these changes is going to carry the most bang for your buck.
[11:33] This really is just another way of thinking about direction.
[11:37] To take a simpler example, if you have some function with two variables as an input,
[11:41] and you compute that its gradient at some particular point comes out as 3,1,
[11:46] then on the one hand you can interpret that as saying that when you're
[11:50] standing at that input, moving along this direction increases the function most quickly,
[11:55] that when you graph the function above the plane of input points,
[11:58] that vector is what's giving you the straight uphill direction.
[12:02] But another way to read that is to say that changes to this first variable have 3
[12:07] times the importance as changes to the second variable,
[12:10] that at least in the neighborhood of the relevant input,
[12:13] nudging the x-value carries a lot more bang for your buck.
[12:19] Let's zoom out and sum up where we are so far.
[12:22] The network itself is this function with 784 inputs and 10 outputs,
[12:27] defined in terms of all these weighted sums.
[12:30] The cost function is a layer of complexity on top of that.
[12:33] It takes the 13,000 weights and biases as inputs and spits out
[12:37] a single measure of lousiness based on the training examples.
[12:42] And the gradient of the cost function is one more layer of complexity still.
[12:47] It tells us what nudges to all these weights and biases cause the
[12:50] fastest change to the value of the cost function,
[12:53] which you might interpret as saying which changes to which weights matter the most.
[13:02] So, when you initialize the network with random weights and biases,
[13:06] and adjust them many times based on this gradient descent process,
[13:09] how well does it actually perform on images it's never seen before?
[13:14] The one I've described here, with the two hidden layers of 16 neurons each,
[13:18] chosen mostly for aesthetic reasons, is not bad,
[13:22] classifying about 96% of the new images it sees correctly.
[13:26] And honestly, if you look at some of the examples it messes up on,
[13:30] you feel compelled to cut it a little slack.
[13:36] Now if you play around with the hidden layer structure and make a couple tweaks,
[13:40] you can get this up to 98%.
[13:41] And that's pretty good!
[13:43] It's not the best, you can certainly get better performance by getting more sophisticated
[13:47] than this plain vanilla network, but given how daunting the initial task is,
[13:52] I think there's something incredible about any network doing this well on images it's
[13:56] never seen before, given that we never specifically told it what patterns to look for.
[14:02] Originally, the way I motivated this structure was by describing a hope we might have,
[14:06] that the second layer might pick up on little edges,
[14:09] that the third layer would piece together those edges to recognize loops
[14:13] and longer lines, and that those might be pieced together to recognize digits.
[14:17] So is this what our network is actually doing?
[14:21] Well, for this one at least, not at all.
[14:24] Remember how last video we looked at how the weights of the connections from all
[14:28] the neurons in the first layer to a given neuron in the second layer can be
[14:32] visualized as a given pixel pattern that the second layer neuron is picking up on?
[14:37] Well, when we actually do that for the weights associated with these transitions,
[14:42] from the first layer to the next, instead of picking up on isolated little edges here
[14:47] and there, they look, well, almost random, just with some very loose patterns in the
[14:52] middle there.
[14:53] It would seem that in the unfathomably large 13,000 dimensional space
[14:57] of possible weights and biases, our network found itself a happy
[15:01] little local minimum that, despite successfully classifying most images,
[15:05] doesn't exactly pick up on the patterns we might have hoped for.
[15:09] And to really drive this point home, watch what happens when you input a random image.
[15:14] If the system was smart, you might expect it to feel uncertain,
[15:18] maybe not really activating any of those 10 output neurons or activating them
[15:23] all evenly, but instead it confidently gives you some nonsense answer,
[15:27] as if it feels as sure that this random noise is a 5 as it does that an actual
[15:32] image of a 5 is a 5.
[15:34] Phrased differently, even if this network can recognize digits pretty well,
[15:38] it has no idea how to draw them.
[15:41] A lot of this is because it's such a tightly constrained training setup.
[15:45] I mean, put yourself in the network's shoes here.
[15:48] From its point of view, the entire universe consists of nothing but clearly
[15:52] defined unmoving digits centered in a tiny grid,
[15:55] and its cost function never gave it any incentive to be anything but utterly
[15:59] confident in its decisions.
[16:02] So with this as the image of what those second layer neurons are really doing,
[16:05] you might wonder why I would introduce this network with the
[16:07] motivation of picking up on edges and patterns.
[16:09] I mean, that's just not at all what it ends up doing.
[16:13] Well, this is not meant to be our end goal, but instead a starting point.
[16:17] Frankly, this is old technology, the kind researched in the 80s and 90s,
[16:21] and you do need to understand it before you can understand more detailed modern
[16:25] variants, and it clearly is capable of solving some interesting problems,
[16:29] but the more you dig into what those hidden layers are really doing,
[16:33] the less intelligent it seems.
[16:38] Shifting the focus for a moment from how networks learn to how you learn,
[16:42] that'll only happen if you engage actively with the material here somehow.
[16:47] One pretty simple thing I want you to do is just pause right now and think deeply
[16:51] for a moment about what changes you might make to this system and how it perceives
[16:56] images if you wanted it to better pick up on things like edges and patterns.
[17:01] But better than that, to actually engage with the material,
[17:04] I highly recommend the book by Michael Nielsen on deep learning and neural networks.
[17:09] In it, you can find the code and the data to download and play with for this exact
[17:14] example, and the book will walk you through step by step what that code is doing.
[17:19] What's awesome is that this book is free and publicly available,
[17:22] so if you do get something out of it, consider joining me in making a donation towards
[17:26] Nielsen's efforts.
[17:27] I've also linked a couple other resources I like a lot in the description,
[17:31] including the phenomenal and beautiful blog post by Chris Ola and the articles in
[17:36] Distill.
[17:38] To close things off here for the last few minutes,
[17:40] I want to jump back into a snippet of the interview I had with Leisha Lee.
[17:44] You might remember her from the last video, she did her PhD work in deep learning.
[17:48] In this little snippet she talks about two recent papers that really dig into
[17:52] how some of the more modern image recognition networks are actually learning.
[17:56] Just to set up where we were in the conversation,
[17:58] the first paper took one of these particularly deep neural networks that's really good
[18:02] at image recognition, and instead of training it on a properly labeled dataset,
[18:06] shuffled all the labels around before training.
[18:09] Obviously the testing accuracy here was going to be no better than random,
[18:13] since everything's just randomly labeled. But it was still able to achieve
[18:17] the same training accuracy as you would on a properly labeled dataset.
[18:21] Basically, the millions of weights for this particular network were
[18:25] enough for it to just memorize the random data,
[18:27] which raises the question for whether minimizing this cost function
[18:31] actually corresponds to any sort of structure in the image, or is it just memorization?
[18:51] ...to memorize the entire dataset of what the correct classification is.
[18:54] And so half a year later at ICML this year, there was not exactly rebuttal paper,
[18:57] but paper that addressed some aspects of like, hey,
[18:59] actually these networks are doing something a little bit smarter than that.
[19:03] If you look at that accuracy curve if you were just training on a random data set
[19:06] that curve went down very slowly, almost in a linear fashion.
[19:08] So you’re really struggling to find that local minimum of the right weights.
[19:12] Whereas if you're actually training on a structured dataset,
[19:15] one that has the right labels, you fiddle around a little bit in the beginning,
[19:20] but then you kind of dropped very fast to get to that accuracy level,
[19:24] and so in some sense it was easier to find that local maxima.
[19:28] And so what was also interesting about that is it brings into light another paper from
[19:33] actually a couple of years ago, which has a lot more simplifications about the network
[19:38] layers, but one of the results was saying how if you look at the optimization landscape,
[19:43] the local minima that these networks tend to learn are actually of equal quality,
[19:48] so in some sense if your dataset is structured,
[19:51] you should be able to find that much more easily.
[19:58] My thanks, as always, to those of you supporting on Patreon.
[20:01] I've said before just what a game changer Patreon is,
[20:04] but these videos really would not be possible without you.
[20:07] I also want to give a special thanks to the VC firm Amplify Partners
[20:10] and their support of these initial videos in the series. Thank you.
