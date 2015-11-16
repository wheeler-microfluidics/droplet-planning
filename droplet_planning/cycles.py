import itertools

import numpy as np


def test_p_fast(nodes, connections):
    '''
    Test if each node in the provided permutation is connected to its right
    neighbour.
    '''
    neighbour_nodes = nodes[1:] + nodes[:1]
    return map(lambda v: connections[tuple(v)],
               itertools.izip(nodes, neighbour_nodes))


def find_cycle_enumerate(nodes, connections, test_f=test_p_fast, findall=False):
    '''
    Find a permutation of the provided list of node indexes that form a cycle
    based on the connections between nodes.

    An exhaustive search is performed and a `ValueError` is raised if no cycle
    exists between the provided nodes.

    __NB__, The runtime of this algorithm is $O(n!)$, which becomes large
    *really* quickly (i.e., for small values $n$).  This function is only
    really practical for up to 10 nodes.
    '''
    solutions = []
    for p in itertools.permutations(nodes[1:], len(nodes) - 1):
        order = (nodes[0], ) + p
        v_connected = test_f(order, connections)
        if sum(v_connected) == nodes.size:
            if not findall:
                return order
            solutions.append(order)
    else:  # No break
        if not findall:
            raise ValueError('No cycle exists between nodes.')
    return solutions


def find_cycle_anneal(nodes, connections, starting_temperature=1,
                      retry_count=15, inner_num=5):
    '''
    Use simple simulated annealing pass to attempt to find a permutation of the
    provided list of node indexes that form a cycle based on the connections
    between nodes.

    A `ValueError` is raised if no cycle is found between the provided nodes.
    However, since the search is not exhaustive, a cycle may still actually
    exist.

    __NB__, The worst case runtime of this algorithm is $O(10000n)$.  Although
    this function does not guarantee a solution if one exists, it remains
    practical for $n > 10$, as opposed to the `find_cycle_enumerate` function.
    '''
    nodes_i = np.array(nodes, dtype=int)
    score_i = sum(test_p_fast(nodes_i, connections))
    if score_i >= len(nodes_i):
        return nodes_i
    temperature = starting_temperature

    for retry_i in xrange(retry_count):
        for i in xrange(100):
            swaps_evaluated = 0
            swaps_accepted = 0

            for j in xrange(int(inner_num * len(nodes) ** 1.333)):
                source, target = np.random.randint(1, len(nodes_i), size=2)
                nodes_j = nodes_i.copy()
                nodes_j[[source, target]] = nodes_i[[target, source]]
                connected = test_p_fast(nodes_j, connections)
                score_j = sum(connected)
                if score_j >= len(nodes):
                    return nodes_j

                keep_anyway = (np.random.rand() <
                               np.power(np.e, (.5 * (score_j - score_i) /
                                               temperature)))

                if score_j >= score_i or keep_anyway:
                    nodes_i = nodes_j
                    score_i = score_j
                    swaps_accepted += 1
                swaps_evaluated += 1

            success_ratio = swaps_accepted / float(swaps_evaluated)

            if success_ratio > .96:
                temperature *= .5
            elif success_ratio > .8:
                temperature *= .9
            elif success_ratio > .15:
                temperature *= .95
            else:
                temperature *= .8
            if i % 10 == 0:
                print 'temperature: %s, success: %.2f' % (temperature,
                                                          success_ratio)
        raise ValueError('No cycle found (score: %s) %s' % (score_i, nodes_i))
