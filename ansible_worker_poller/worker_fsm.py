
from gevent_fsm.fsm import State, transitions

from . import messages


class _Start(State):

    @transitions('Waiting')
    def start(self, controller):

        controller.changeState(Waiting)


Start = _Start()


class _Errored(State):

    @transitions('Waiting')
    def start(self, controller):

        controller.changeState(Waiting)


Errored = _Errored()


class _Waiting(State):

    def start(self, controller):
        if not controller.context.buffered_messages.empty():
            controller.context.queue.put(controller.context.buffered_messages.get())

    @transitions('Running')
    def onDeploy(self, controller, message_type, message):

        controller.changeState(Running)
        controller.context.run_id = message.id
        controller.context.deploy(message.data)

    def onCancel(self, controller, message_type, message):
        print("Ignore Cancel before running")


Waiting = _Waiting()


class _Running(State):

    @transitions('Completed')
    def onComplete(self, controller, message_type, message):

        controller.changeState(Completed)

    @transitions('Errored')
    def onError(self, controller, message_type, message):

        controller.changeState(Errored)

    def onCancel(self, controller, message_type, message):
        controller.changeState(Cancelling)


Running = _Running()


class _Cancelling(State):

    def start(self, controller):
        print("Cancelling")
        controller.context.cancel_requested = True

    @transitions('Completed')
    def onComplete(self, controller, message_type, message):

        controller.changeState(Cancelled)

    @transitions('Errored')
    def onError(self, controller, message_type, message):

        controller.changeState(Cancelled)

    def onCancel(self, controller, message_type, message):
        print("Ignore duplicate Cancel")


Cancelling = _Cancelling()


class _Completed(State):

    @transitions('Waiting')
    def start(self, controller):

        controller.changeState(Waiting)


Completed = _Completed()


class _Cancelled(State):

    @transitions('Waiting')
    def start(self, controller):

        controller.outboxes['output'].put(messages.RunnerCancelled(controller.context.run_id))
        controller.changeState(Waiting)


Cancelled = _Cancelled()
