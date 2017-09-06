
def value_of_feed(profile_rate, count_of_rates, share_success_ratio):
    return share_success_ratio * (1 - 1/(count_of_rates + 1)) * ((min(profile_rate, 1)/5)**2) * 2147483647
