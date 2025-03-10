import torch
import itertools
import numpy as np

class SINDyLibrary():
    def __init__(self,
                 latent_dim=3,
                 include_biases=True,
                 include_states=True,
                 include_sin=True,
                 include_cos=True,
                 poly_order=1,
                 include_sqrt=False,
                 include_inverse=False,
                 include_exp=False,
                 include_sign_sqrt_of_diff=False,
                 device='cuda:0'):

        self.device = device
        self.candidate_functions = []
        self.feature_names = []
        # initialize lib with biasses
        self.latent_dim = latent_dim

        self.include_biases = include_biases
        self.include_states = include_states
        self.include_sin = include_sin
        self.include_cos = include_cos
        self.include_exp = include_exp
        self.include_inverse = include_inverse
        self.poly_order = poly_order
        self.include_sqrt = include_sqrt
        self.include_singn_sqrt_of_diff = include_sign_sqrt_of_diff

        # fit for functions and feature names
        self.fit()
        self.number_candidate_functions = len(self.feature_names)

    def biases(self, z):
        return torch.ones(z.shape[0], 1, device=self.device)

    @staticmethod
    def states(z):
        return z

    @staticmethod
    def sin(z):
        return - torch.sin(z)

    @staticmethod
    def cos(z):
        return torch.cos(z)

    def multiply_pairs(self, z):
        result = []
        # for idx1, idx2 in self.idx_combis_commutative:
        #     res = z[:, idx1] * z[:, idx2]
        #     res = res.reshape(-1, 1)
        #     result.append(res)
        result = z[:, self.idx_new[0]] * z[:, self.idx_new[1]]
        return result
        # return torch.cat(result, axis=1)

    @staticmethod
    def inverse(z):
        return 1 / (z + 1e-4)

    def poly_deg_2(self, z):
        result = z[:, self.idx_new[0]] * z[:, self.idx_new[1]]
        return result

    @staticmethod
    def sqrt(z):
        return torch.sqrt(z)

    @staticmethod
    def exp(z):
        return torch.exp(z)

    def sing_sqrt_diff_pairs(self, z):
        result = []
        for idx1, idx2 in self.idx_combis_commutative:
            res = torch.sign(z[:, idx1] - z[:, idx2]) * torch.sqrt(torch.abs(z[:, idx1] - z[:, idx2]))
            res = res.reshape(-1, 1)
            result.append(res)
        return torch.cat(result, axis=1)

    def fit(self):
        ## generate all possible pairs of z variable indices
        possible_indicies = list(range(self.latent_dim))
        permuts = itertools.product(possible_indicies, possible_indicies)
        permuts = [p for p in permuts if not p[0] == p[1]]
        self.idx_combis_non_commutative = permuts
        self.idx_combis_commutative = list(set([tuple(sorted(list(p))) for p in permuts]))

        self.idx_new = np.triu_indices(self.latent_dim)

        if self.include_biases:
            self.candidate_functions.append(self.biases)
            names = ['1']
            self.feature_names.extend(names)
        if self.include_states:
            self.candidate_functions.append(self.states)
            names = [f'z{i}' for i in range(self.latent_dim)]
            self.feature_names.extend(names)
        if self.include_sin:
            self.candidate_functions.append(self.sin)
            names = [f'sin(z{i})' for i in range(self.latent_dim)]
            self.feature_names.extend(names)
        if self.include_cos:
            self.candidate_functions.append(self.cos)
            names = [f'cos(z{i})' for i in range(self.latent_dim)]
            self.feature_names.extend(names)
        if self.include_inverse:
            self.candidate_functions.append(self.inverse)
            names = [f'1/z{i}' for i in range(self.latent_dim)]
            self.feature_names.extend(names)
        if self.poly_order == 2:
            self.candidate_functions.append(self.poly_deg_2)
            names = [f'z{idx1}*z{idx2}' for idx1, idx2 in zip(self.idx_new[0], self.idx_new[1])]
            self.feature_names.extend(names)
        if self.include_sqrt:
            self.candidate_functions.append(self.sqrt)
            names = [f'sqrt(z{i})' for i in range(self.latent_dim)]
            self.feature_names.extend(names)
        if self.include_exp:
            self.candidate_functions.append(self.exp)
            names = [f'exp(z{i})' for i in range(self.latent_dim)]
            self.feature_names.extend(names)
        if self.include_singn_sqrt_of_diff:
            self.candidate_functions.append(self.sing_sqrt_diff_pairs)
            names = [f'sign(z{idx1}-z{idx2})*sqrt(|z{idx1}-z{idx2}|)'
                     for idx1, idx2 in self.idx_combis_commutative]
            self.feature_names.extend(names)

    def get_feature_names(self, ):
        return self.feature_names

    def transform(self, z):
        theta = [cand_func(z) for cand_func in self.candidate_functions]
        out = torch.cat(theta, axis=1)
        return out


if __name__ == '__main__':
    # some test for the SINDy lib
    import torch

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    z = torch.tensor([[1, 2, 3], [4, 0, 6]]).to(device)
    sl = SINDyLibrary()
    theta = sl.transform(z)
    print(sl.feature_names)
    print(theta)
