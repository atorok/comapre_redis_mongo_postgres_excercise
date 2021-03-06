# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the lines above. See PEP 8, PEP 263.
"""
 Load the legacy data in redis

 Possible improovement: load specific allowing rules for any prefix that is
 not restricted.

 This would make it possible to invalidate a None result form redis
 would help if for some reason the script or the data in redis are
 corrupted / missing and no rule is found, we could still
 preventively block calls ( even trough we might be over blocking )
 to prevent excessive costs.
"""
import redis
import argparse
from phone_rule_engine import RuleOperations
import phone_legacy_data


def parse_args():
    parser = argparse.ArgumentParser(
        description='Import the hardcoded data into redis'
    )
    parser.add_argument("--host", default="localhost",
                        help="redis host to connect to")
    parser.add_argument("--port", default="6379",
                        help="redis port to connect to")
    return parser.parse_args()


def check_for_existing(rule_ops, samples):
    return any((
        rule_ops.query_rule(prefix) is not None for prefix in samples
    ))


def main():
    args = parse_args()
    rule_ops = RuleOperations(
        redis.StrictRedis(host=args.host, port=args.port)
    )
    generic_restrictions = sorted(phone_legacy_data.RESTRICTED_OUTBOUND_PAYING_PREFIXES.keys())

    if check_for_existing(rule_ops, (generic_restrictions[0], generic_restrictions[10])):
        print("Rules were already laoded. Refusign to do any changes")
        return

    for prefix in generic_restrictions:
        rule_ops.push_generic_rule(prefix, rule_ops.R_RESTRICT)
        # add the rule as a prefix rule as well to speed up queries for trial
        # users.
        # this will avoid some redis lookups at the expense fo using up more
        # memory
        rule_ops.push_trial_rule(prefix, rule_ops.R_RESTRICT)
    print("Imported {} general rules".format(
        len(generic_restrictions)
    ))

    trial_restrictions=phone_legacy_data.RESTRICTED_OUTBOUND_TRIAL_PREFIXES.keys()
    for prefix in trial_restrictions:
        rule_ops.push_trial_rule(prefix, rule_ops.R_RESTRICT)
    print("Imported {} trial rules".format(
        len(trial_restrictions)
    ))

if __name__ == "__main__":
    main()
