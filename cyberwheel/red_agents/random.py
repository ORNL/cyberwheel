import random


class RandomRedAgent:
    def __init__(self, network):
        self.network = network
        self.current_host = self.network.get_random_host()
        self.target = self.network.find_host_with_longest_path(self.current_host)

    def act(self):
        # If the current host is the target, we're done
        if self.current_host == self.target:
            return

        # If the current host is no longer compromised, set it to a compromised host
        if not self.network.check_compromised_status(self.current_host):
            self.current_host = self.network.get_random_compromised_host()

        # Get the neighbors of the current host
        neighbors = self.network.get_neighbors(self.current_host)

        # If there are no neighbors, discover new subnets
        if not neighbors:
            new_subnets = self.network.discover_subnets(self.current_host)
            for subnet in new_subnets:
                self.network.add_subnet(subnet)
            neighbors = self.network.get_neighbors(self.current_host)

        # Search all neighbors and compromise the first uncompromised host
        for neighbor in neighbors:
            if not self.network.check_compromised_status(neighbor):
                self.network.update_host_compromised_status(neighbor, True)
                self.current_host = neighbor
                break
        else:
            # If all neighbors are compromised, move to a random neighbor
            self.current_host = random.choice(neighbors)
