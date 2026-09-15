---
video_id: CqOfi41LfDw
url: https://www.youtube.com/watch?v=CqOfi41LfDw
title: The Essential Main Ideas of Neural Networks
channel: StatQuest with Josh Starmer
duration: 18:54
language: en
unit: L15
status: OK
---

[00:00] Neural networks...
[00:04] seem so complicated, but they're not!
[00:09] StatQuest!
[00:11] Hello!
[00:13] I'm Josh Starmer and welcome to StatQuest!
[00:15] Today, we're going to talk about neural networks, part one: inside the black box!
[00:22] Neural networks, one of the most popular algorithms in machine learning, cover a broad range of concepts and techniques.
[00:31] however, people call them a black box because it can be hard to understand what they're doing.
[00:38] the goal of this series is to take a peek into the black box by breaking down each
[00:44] concept and technique into its components and walking through how they fit together, step by step.
[00:51] in this first part, we will learn about what neural networks do, and how they do it.
[00:57] in part two, we'll talk about how neural networks are fit to data with backpropagation.
[01:04] then, we will talk about variations on the simple neural network presented in this part, including deep learning.
[01:12] note: crazy awesome news!
[01:16] i have a new way to think about neural networks that will help beginners and seasoned
[01:21] experts alike gain a deep insight into what neural networks do.
[01:27] for example, most tutorials use cool looking, but hard to understand graphs, and fancy
[01:34] mathematical notation to represent neural networks.
[01:39] in contrast, i'm going to label every little thing on the neural network to make it easy to keep track of the details.
[01:48] and the math will be as simple as possible, while still being true to the algorithm.
[01:54] these differences will help you develop a deep understanding of what neural networks actually do.
[02:02] so, with that said, let's imagine we tested a drug that was designed to treat an illness
[02:09] and we gave the drug to three different groups of people, with three different dosages: low, medium, and high.
[02:20] the low dosages were not effective so we set them to zero on this graph. in contrast,
[02:27] the medium dosages were effective so we set them to one.
[02:32] and the high dosages were not effective, so those are set to zero.
[02:38] now that we have this data, we would like to use it to predict whether or not a future dosage will be effective.
[02:46] however we can't just fit a straight line to the data to make predictions, because
[02:51] no matter how we rotate the straight line, it can only accurately predict two of the three dosages.
[02:59] the good news is that a neural network can fit a squiggle to the data.
[03:05] the green squiggle is close to zero for low dosages, close to one for medium dosages,
[03:12] and close to zero for high dosages. and even if we have a really complicated dataset
[03:20] like this, a neural network can fit a squiggle to it.
[03:26] in this StatQuest we're going to use this super simple dataset and show how this neural network creates this green squiggle.
[03:36] but first, let's just talk about what a neural network is.
[03:42] a neural network consists of nodes and connections between the nodes.
[03:49] note: the numbers along each connection represent parameter values that were estimated
[03:54] when this neural network was fit to the data.
[03:58] for now, just know that these parameter estimates are analogous to the slope and intercept
[04:04] values that we solve for when we fit a straight line to data.
[04:09] likewise, a neural network starts out with unknown parameter values that are estimated
[04:15] when we fit the neural network to a dataset using a method called backpropagation.
[04:21] and we will talk about how backpropagation estimates these parameters in part 2 in this series.
[04:29] but, for now, just assume that we've already fit this neural network to this specific
[04:35] dataset, and that means we have already estimated these parameters.
[04:41] also, you may have noticed that some of the nodes have curved lines inside of them.
[04:48] these bent or curved lines are the building blocks for fitting a squiggle to data.
[04:55] the goal of this StatQuest is to show you how these identical curves can be reshaped
[05:01] by the parameter values and then added together to get a green squiggle that fits the data.
[05:09] note: there are many common bent or curved lines that we can choose for a neural network.
[05:16] this specific curved line is called soft plus, which sounds like a brand of toilet paper.
[05:23] alternatively, we could use this bent line, called ReLU, which is short for rectified linear unit, and sounds like a robot.
[05:33] or, we could use a sigmoid shape, or any other bent or curved line.
[05:39] oh no!
[05:40] it's the dreaded terminology alert!
[05:43] the curved or bent lines are called activation functions.
[05:48] when you build a neural network you have to decide which activation function, or functions, you want to use.
[05:57] when most people teach neural networks they use the sigmoid activation function.
[06:03] however, in practice, it is much more common to use the ReLU activation function, or the soft plus activation function.
[06:13] so we'll use the soft plus activation function in this StatQuest.
[06:18] anyway, we'll talk more about how you choose activation functions later in this series.
[06:25] note: this specific neural network is about as simple as they get.
[06:31] it only has one input node, where we plug in the dosage, only one output node to tell
[06:37] us the predicted effectiveness, and only two nodes between the input and output nodes.
[06:44] however, in practice, neural networks are usually much fancier and have more than
[06:51] one input node, more than one output node, different layers of nodes between the
[06:57] input and output nodes, and a spider web of connections between each layer of nodes.
[07:06] oh no!
[07:07] it's another terminology alert!
[07:09] these layers of nodes between the input and output nodes are called hidden layers.
[07:16] when you build a neural network one of the first things you do is decide how many
[07:21] hidden layers you want and how many nodes go into each hidden layer.
[07:26] although there are rules of thumb for making decisions about the hidden layers, you
[07:31] essentially make a guess and see how well the neural network performs, adding more layers and nodes if needed.
[07:40] now, even though this neural network looks fancy, it is still made from the same parts
[07:47] used in this simple neural network, which has only one hidden layer with two nodes.
[07:55] so let's learn how this neural network creates new shapes from the curved or bent
[08:00] lines in the hidden layer, and then adds them together to get a green squiggle that fits the data.
[08:08] note: to keep the math simple, let's assume dosages go from zero, for low, to one, for high.
[08:18] the first thing we are going to do is plug the lowest dosage, zero, into the neural network.
[08:25] now, to get from the input node to the top node in the hidden layer, this connection
[08:32] multiplies the dosage by negative 34.4 and then adds 2.14, and the result is an x-axis coordinate for the activation function.
[08:47] for example, the lowest dosage 0 is multiplied by negative 34.4, and then we add 2.14,
[08:57] to get 2.14 as the x-axis coordinate for the activation function.
[09:06] to get the corresponding y-axis value we plug 2.14 into the activation function, which in this case is the soft plus function.
[09:18] note: if we had chosen the sigmoid curve for the activation function then we would
[09:23] plug 2.14 into the equation for the sigmoid curve.
[09:29] and if we had chosen the ReLU bent line for the activation function, then we would plug 2.14 into the ReLU equation.
[09:39] but, since we are using soft plus for the activation function, we plug 2.14 into the soft plus equation.
[09:48] and the log of one plus e raised to the 2.14 power is 2.25.
[09:57] note: in statistics, machine learning, and most programming languages, the log function
[10:04] implies the natural log, or the log base e. anyway, the y-axis coordinate for the
[10:11] activation function is 2.25, so let's extend this y-axis up a little bit and put
[10:19] a blue dot at 2.25 for when dosage equals zero.
[10:26] now, if we increase the dosage a little bit and plug 0.1 into the input, the x-axis
[10:34] coordinate for the activation function is negative 1.3, and the corresponding y-axis
[10:41] value is 0.24. so, let's put a blue dot at 0.24 for when dosage equals 0.1. and,
[10:52] if we continue to increase the dosage values all the way to 1, the maximum dosage, we get this blue curve.
[11:02] note: before we move on I want to point out that the full range of dosage values,
[11:08] from 0 to 1, corresponds to this relatively narrow range of values from the activation function.
[11:16] in other words, when we plug dosage values, from 0 to 1, into the neural network,
[11:23] and then multiply them by negative 34.4 and add 2.14, we only get x-axis coordinates that are within the red box.
[11:35] and thus, only the corresponding y-axis values in the red box are used to make this new blue curve.
[11:44] bam!
[11:45] now we scale the y-axis values for the blue curve by negative 1.3. for example, when
[11:53] dosage equals zero the current y-axis coordinate for the blue curve is 2.25, so we
[12:01] multiply 2.25 by negative 1.3 and get negative 2.93. and negative 2.93 corresponds to this position on the y-axis.
[12:16] likewise, we multiply all of the other y-axis coordinates on the blue curve by negative
[12:23] 1.3 and we end up with a new blue curve.
[12:27] bam!
[12:30] now, let's focus on the connection from the input node, to the bottom node in the hidden layer.
[12:37] however, this time, we multiply the dosage by negative 2.52, instead of negative 34.4,
[12:47] and we add 1.29, instead of 2.14, to get the x-axis coordinate for the activation function.
[12:58] remember, these values come from fitting the neural network to the data with backpropagation,
[13:05] and we'll talk about that in part two in this series.
[13:09] now, if we plug the lowest dosage, zero, into the neural network, then the x-axis
[13:16] coordinate for the activation function is 1.29.
[13:21] now we plug 1.29 into the activation function to get the corresponding y-axis value,
[13:30] and get 1.53. and that corresponds to this yellow dot.
[13:37] now, we just plug in dosage values from 0 to 1 to get the corresponding y-axis values, and we get this orange curve.
[13:48] note: just like before, i want to point out that the full range of dosage values,
[13:54] from 0 to 1, corresponds to this narrow range of values from the activation function.
[14:01] in other words, when we plug dosage values from 0 to 1 into the neural network we
[14:08] only get x-axis coordinates that are within the red box.
[14:14] and thus, only the corresponding y-axis values in the red box are used to make this new orange curve.
[14:22] so we see that fitting a neural network to data gives us different parameter estimates
[14:28] on the connections and that results in each node in the hidden layer using different
[14:34] portions of the activation functions to create these new and exciting shapes.
[14:40] now, just like before, we scale the y-axis coordinates on the orange curve, only this
[14:46] time we scale by a positive number: 2.28.
[14:50] beep boop beep! for every number written on the screen] and that gives us this new orange curve.
[14:59] now the neural network tells us to add the y-axis coordinates from the blue curve
[15:06] to the orange curve, and that gives us this green squiggle.
[15:11] then, finally, we subtract 0.58 from the y-axis values on the green squiggle, and
[15:19] we have a green squiggle that fits the data.
[15:23] bam!
[15:25] now, if someone comes along and says that they are using dosage equal to 0.5 we can
[15:32] look at the corresponding y-axis coordinate on the green squiggle and see that the dosage will be effective.
[15:39] or, we can solve for the y-axis coordinate by plugging dosage equals 0.5 into the neural network, and do the math.
[16:08] [Music] and we see that the y-axis coordinate on the green squiggle is 1.03, and since
[16:19] 1.03 is closer to 1 than 0, we will conclude that a dosage equal to 0.5 is effective.
[16:35] double bam!
[16:39] now, if you've made it this far you may be wondering why this is called a neural network.
[16:45] instead of a big fancy squiggle fitting machine.
[16:49] the reason is that way back in the 1940s and 50s, when neural networks were invented,
[16:56] they thought the nodes were vaguely like neurons, and the connections between the nodes were sort of like synapses.
[17:04] however, i think they should be called big fancy squiggle fitting machines, because that's what they do.
[17:11] note: whether or not you call it a squiggle fitting machine, the parameters that we
[17:17] multiply are called weights, and the parameters that we add are called biases.
[17:23] note: this neural network starts with two identical activation functions, but the
[17:29] weights and biases on the connections slice them, flip them, and stretch them into
[17:35] new shapes, which are then added together to get a squiggle that is entirely new.
[17:41] and then the squiggle is shifted to fit the data.
[17:45] now, if we can create this green squiggle with just two nodes in a single hidden layer,
[17:50] just imagine what types of green squiggles we could fit with more hidden layers and more nodes in each hidden layer.
[17:58] in theory, neural networks can fit a green squiggle to just about any dataset, no
[18:04] matter how complicated, and i think that's pretty cool.
[18:08] triple bam!
[18:12] now it's time for some shameless self-promotion!
[18:17] if you want to review statistics and machine learning offline check out the StatQuest study guides at statquest.org.
[18:25] there's something for everyone.
[18:28] hooray!
[18:29] we've made it to the end of another exciting StatQuest.
[18:32] if you like this StatQuest and want to see more, please subscribe.
[18:36] and if you want to support StatQuest consider contributing to my patreon campaign,
[18:41] becoming a channel member, buying one or two of my original songs, or a t-shirt, or a hoodie, or just donate.
[18:48] the links are in the description below.
[18:50] alright, until next time.
[18:52] quest on!
