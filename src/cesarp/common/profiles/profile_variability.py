#
# Copyright (c) 2022, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
#
# This file is part of CESAR-P - Combined Energy Simulation And Retrofit written in Python
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Contact: https://www.empa.ch/web/s313
#
import random
import numpy.random
from scipy.optimize import fsolve
from pint import Quantity

from cesarp.common.profiles import DAYS_PER_YEAR, HOURS_PER_DAY, HOURS_PER_YEAR

FRACTION_PROF_MIN_VAL = 0
FRACTION_PROF_MAX_VAL = 1


def expand_value_to_variable_profile(value, band, profile_length=DAYS_PER_YEAR):
    """
    creates a profile with randomized (discrete uniform) entries of value

    :param value: value to use as the base for the random values
    :param band: value+/-band is used as space for random number generation, band is an absolute number
    :param profile_length: number of profile entries to generate
    :return: list of randomized values with lenght profile_length

    """
    return numpy.random.randint((value - band), (value + band + 1 * value.u), size=profile_length) * value.u


def randomize_vertical(values, band, min_value=FRACTION_PROF_MIN_VAL, max_value=FRACTION_PROF_MAX_VAL):
    """
    Create a new list of values by taking each original value and generating a random number in the range of value +/- band

    :param values: list with values
    :param band: +/-band used to generate randomness for the values
    :param min_value: limit for resulting values, default is FRACTION_PROF_MIN_VAL=0
    :param max_value: limit for resulting values, default is FRACTION_PROF_MAX_VAL=1
    :return: list of randomized values with same length as input

    """
    lower_bounds = [val - band for val in values]
    upper_bounds = [val + band for val in values]
    rand_nums = numpy.random.uniform(low=lower_bounds, high=upper_bounds)
    rand_nums = [max(min(rand_num, max_value), min_value) for rand_num in rand_nums]
    return rand_nums


def horizontal_variability(year_profile_hourly, breaks_per_day):
    """
    For each day (24 hours) in the profile for the blocks according to the hours defined in breaks the profile entries are shuffled.

    :param profile: profile for one year, hourly values
    :param breaks_per_day: list of hours of the day defining blocks of profiles to shuffle;
                            breaks refer to one day;
                            spanning over night to next day is possible, eg breaks 8, 17, 20, resulting blocks are 9-17h and 21-8h;
                            if empty no shuffling is performed;
    :return: profile with blocks shuffled

    """
    assert len(year_profile_hourly) == HOURS_PER_YEAR, f"profile should have {HOURS_PER_YEAR} entries, but has {len(year_profile_hourly)}"

    if not breaks_per_day:
        return year_profile_hourly.copy()

    break_indexes_whole_year = [day_index * HOURS_PER_DAY + break_hour for day_index in range(0, DAYS_PER_YEAR) for break_hour in breaks_per_day]
    if break_indexes_whole_year[-1] != HOURS_PER_YEAR:
        break_indexes_whole_year.append(HOURS_PER_YEAR)

    profile_blockwise_shuffled = list()
    break_index_start = 0
    for break_index_end in break_indexes_whole_year:
        block = year_profile_hourly[break_index_start:break_index_end]  # result does not include break_index_end
        random.shuffle(block)
        profile_blockwise_shuffled.extend(block)
        break_index_start = break_index_end

    return profile_blockwise_shuffled


def get_random_value_triangular_dist(min, max, peak):
    """
    Arguments can be either passed as plain number or as pint.Quantity objects, in latter case the random value is also returned as pint.Quantity with same unit.
    Either all or non of the arguments need to be of type pint.Quantity!

    :param min: minimum for distribution, equals to parameter "a" of triangular distribution
    :param max: maximum for distribution, equals to parameter "b" of triangular distribution
    :param peak: peak or middle value for distribution, equals to parameter "c" of triangular distribution

    :return: random value drawn from triangular distribution with passed parameters; type is either pint.Quantity or plain number depending on type of the parameters
    """
    if min == peak and peak == max:  # min, std, max have same value -> no variability
        value_var = peak
    else:
        unit = 1
        if isinstance(min, Quantity):
            unit = min.u
            min = min.m
            peak = peak.m
            max = max.m

        value_var = numpy.random.triangular(left=min, mode=peak, right=max, size=1)[0] * unit
    return value_var


def triang_dist_limits(target_min, target_max, peak, perc=0.05):
    """
    Returns a, b, c to be used for a triangular distribution's parameters so that values below/above "target_min" resp "target_max" occur with "perc" probability.
    The reason for using this definition for a, b instead of using directly target_min, target_max as a, b is that a, b have a probability of occurance of almost zero and
    if you want to cover the values range between target_min and target_max you might want a higher probability of occurance for target_min, target_max.

    :param target_min: value which should be the "perc" percentile in the distribution
    :param target_max: value which should be the 1-"perc" percentile in the distribution
    :param peak: corresponds to the peak value in the distribution, respectively c
    :param perc: percentile at which to set target_min resp target_max

    :return tuple(a,b,c) resp (min, max, peak) to be used as parameters for a triangular distribution, e.g. those can be passed to get_random_value_triangular_dist()
    """

    if target_min == peak and peak == target_max:
        return (target_min, target_max, peak)

    def triang_cdf(x):
        """
        CDF (cumulative distribution function) for triangular distribution.
        See: https://en.wikipedia.org/wiki/Triangular_distribution
        """
        # eq 1: replace x of the CDF with target_min, use CDF for a < x <= c, set it equal to perc; F(target_min) = perc = (target_min - a)^2 / ((b-a)(c-a))
        # eq 2: replace x of the CDF with target_max, use CDF for c < x < b, set it equal to 1-perc; F(target_max) = 1-perc = 1- [(b - target_max)^2/((b-a)(b-c))
        # a, b of a distribution matching that criteria is unknown, so set a, b as x[0], x[1]; c=peak
        return [
            ((target_min - x[0]) ** 2) / (x[1] - x[0]) / (peak - x[0]) - perc,
            ((x[1] - target_max) ** 2) / (x[1] - x[0]) / (x[1] - peak) - perc,
        ]

    x = fsolve(triang_cdf, x0=[target_min - 1, target_max + 1])
    # note that x is an array, where x[0] -> a, x[1] -> b, to be used in the triangular distribution function
    return (x[0], x[1], peak)
