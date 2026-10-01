"""Local acknowledgement is synchronization, never remote evidence."""

from copy import deepcopy
from datetime import datetime, timezone


class OwnerPolicyHandoff:
    """One use, including invalid acknowledgement, expiry and read error."""

    def __init__(self, expected_ack, *, deadline, freshness, clock=None):
        self.expected_ack = deepcopy(expected_ack)
        self.deadline = deadline
        self.freshness = freshness
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.used = False

    def check_time(self):
        now = self.clock()
        if now.utcoffset() is None or not now < self.deadline:
            raise ValueError('V41_OWNER_ACK_EXPIRED')
        self.freshness()

    def observe(self, acknowledge, read_once, validate):
        if self.used:
            raise ValueError('V41_OWNER_ACK_REPLAY')
        self.used = True
        self.check_time()
        ack = acknowledge(self.check_time)
        self.check_time()
        if type(ack) is not dict or ack != self.expected_ack:
            raise ValueError('V41_OWNER_ACK_REFUSED')
        observed = read_once()  # No retry; an exception never means absence.
        self.check_time()
        validate(observed)
        return observed
