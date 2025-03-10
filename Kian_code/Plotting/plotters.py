import numpy as np
import torch
from torch import Tensor
import Double_Pendulum.Lumped_Mass.transforms as transforms
import Double_Pendulum.Lumped_Mass.dynamics as dynamics
from matplotlib import pyplot as plt


def plot_data():
    q1_plot = torch.linspace(-np.pi/2, np.pi/2, 50)
    q2_plot = torch.linspace(-np.pi/2, np.pi/2, 50)
    q1_grid, q2_grid = torch.meshgrid(q1_plot, q2_plot, indexing='ij')
    
    return q1_grid, q2_grid


def plot_3d(x, y, z, plot_title, xlabel, ylabel, zlabel):
    # Create a single 3D plot
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111, projection='3d')
    fig.suptitle(plot_title, fontsize=16, y=0.75)  # General title

    # Plot the surface
    surf = ax.plot_surface(x, y, z, cmap='viridis', edgecolor='none')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)

    # Add colorbar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, orientation='vertical', label=zlabel)
    plt.show()
    
    
def plot_3d_double(x, y, z1, z2, plot_title, title_1, title_2, xlabel, ylabel, zlabel, z_limits = None):
     # Create side-by-side plots
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), subplot_kw={'projection': '3d'})
    #fig.suptitle(plot_title, fontsize=16, y=0.75)  # General title

    # Left plot: Analytic function
    axes[0].plot_surface(x, y, z1, cmap='viridis', edgecolor='none')
    axes[0].set_xlabel(xlabel)
    axes[0].set_ylabel(ylabel)
    axes[0].set_zlabel(zlabel)
    axes[0].set_title(title_1)

    # Apply z-limits if provided
    if z_limits is not None:
        axes[0].set_zlim(z_limits)

    # Right plot: Learned function
    surf = axes[1].plot_surface(x, y, z2, cmap='plasma', edgecolor='none')
    axes[1].set_xlabel(xlabel)
    axes[1].set_ylabel(ylabel)
    axes[1].set_zlabel(zlabel)
    axes[1].set_title(title_2)

    # Add colorbar for both plots
    fig.colorbar(surf, ax=axes, shrink=0.5, aspect=15, orientation='vertical', label='$h_2$')
    plt.show()   
    
    
def plot_h2(model, device, rp, epoch):
    
    q1_grid, q2_grid = plot_data()
    
    h2_analytic = torch.empty_like(q1_grid)
    h2_learned = torch.empty_like(q1_grid)
    for i in range(q1_grid.shape[0]):
        for j in range(q1_grid.shape[1]):
            q_plot = torch.tensor([q1_grid[i, j], q2_grid[i, j]]).to(device)
            h2_analytic[i, j] = transforms.analytic_theta_2(rp, q_plot)
            theta_learned, _  = model.encoder_nn(q_plot)
            h2_learned[i, j] = theta_learned

    # Convert tensors to numpy arrays for plotting
    q1_grid_np = q1_grid.numpy()
    q2_grid_np = q2_grid.numpy()
    h2_analytic_np = h2_analytic.numpy() 
    h2_learned_np = h2_learned.detach().numpy()

    # h2 is defined in learning up to a constant, so remove the average to normalize both
    h2_analytic_norm = h2_analytic_np - h2_analytic_np.mean()
    h2_learned_norm = h2_learned_np - h2_learned_np.mean()
    
    
    plot_title = "Comparison of Analytic and Learned $h_2$ at epoch " + str(epoch + 1)
    title_1 = "Analytic $h_2$"
    title_2 = "Learned $h_2$"
    xlabel = "$q_1$ (rad)"
    ylabel = "$q_2$ (rad)"
    zlabel = "$h_2$ (rad)"
    
    plot_3d_double(q1_grid_np, q2_grid_np, h2_analytic_norm, h2_learned_norm, plot_title, 
                   title_1, title_2, xlabel, ylabel, zlabel)
    
def plot_J_h(model, device, rp, epoch, plot_index):
    
    #Obtain [q1,q1]-grid and flatten
    q1_grid, q2_grid = plot_data()
    q_grid_flat = torch.stack([q1_grid.flatten(), q2_grid.flatten()], dim=-1).to(device)  # Shape: (N, 2)
    
    # Use vmap to vectorize over the grid
    J_h_1_0_analytic_flat = torch.vmap(torch.func.jacfwd(model.encoder_theta_2_ana, has_aux=True))(q_grid_flat)[0][:,:,plot_index]
    J_h_1_0_learned_flat = torch.vmap(torch.func.jacfwd(model.encoder_nn, has_aux=True))(q_grid_flat)[0][:,:,plot_index]

    # Reshape results back to the grid shape
    J_h_1_0_analytic = J_h_1_0_analytic_flat.view(q1_grid.shape)
    J_h_1_0_learned = J_h_1_0_learned_flat.view(q1_grid.shape)

    
    # Convert tensors to numpy arrays for plotting
    q1_grid_np = q1_grid.numpy()
    q2_grid_np = q2_grid.numpy()
    J_h_1_0_analytic_np = J_h_1_0_analytic.cpu().numpy()
    J_h_1_0_learned_np = J_h_1_0_learned.detach().cpu().numpy()
    
    # Plot details
    plot_title = "Comparison of Analytic and Learned $J_h10$ at epoch " + str(epoch + 1)
    title_1 = "Analytic $J_h10$"
    title_2 = "Learned $J_h10$"
    xlabel = "$q_1$ (rad)"
    ylabel = "$q_2$ (rad)"
    zlabel = "$J_h$ (rad)" 
    
    plot_3d_double(q1_grid_np, q2_grid_np, J_h_1_0_analytic_np, J_h_1_0_learned_np, 
                   plot_title, title_1, title_2, xlabel, ylabel, zlabel)
    
def plot_decoupling(model, device, rp, epoch):
    
    #Obtain [q1,q1]-grid and flatten
    q1_grid, q2_grid = plot_data()
    q_grid_flat = torch.stack([q1_grid.flatten(), q2_grid.flatten()], dim=-1).to(device)  # Shape: (N, 2)
    
    theta, J_h, q_hat, J_h_ana = model(q_grid_flat)

    """
    try:
        J_h_inv = torch.linalg.inv(J_h).to(device)
    except:"""
    J_h_inv = torch.linalg.pinv(J_h).to(device)
    J_h_inv_trans = J_h_inv.transpose(1,2).to(device)
    
    matrices_vmap = torch.vmap(dynamics.dynamical_matrices, 
                                   in_dims=(None, 0, 0))

    
    # Inputting q as q_d. This is not pretty but it doesn't matter since we only care about M_q
    M_q, C_q, G_q = matrices_vmap(rp, q_grid_flat, q_grid_flat)
    
        
    M_th, C_th, G_th = transforms.transform_dynamical_matrices(M_q, C_q, G_q, J_h, device)
    M_th_ana, C_th_ana, G_th_ana = transforms.transform_dynamical_matrices(M_q, C_q, G_q, J_h_ana, device)


    matrices_th_ana_vmap = torch.vmap(dynamics.dynamical_matrices_th, 
                                   in_dims=(None, 0, 0))
    M_th_ana, C_th_ana, G_th_ana = matrices_th_ana_vmap(rp, q_grid_flat, q_grid_flat)
    
    off_dia = M_th[:, 0, 1]
    diag_elements = M_th_ana[:, [0, 1], [0, 1]]
    diag_product = torch.sqrt(diag_elements[:, 0] * diag_elements[:, 1])
    try:
        M_th_ratio = off_dia/diag_product
    except:
        print("diag_product is zero")
        diag_product += 1e-8
        M_th_ratio = off_dia/diag_product


    off_dia_ana = M_th_ana[:, 0, 1]
    diag_elements_ana = M_th_ana[:, [0, 1], [0, 1]] 
    diag_product_ana = torch.sqrt(diag_elements_ana[:, 0] * diag_elements_ana[:, 1])

    try:
        M_th_ratio_ana = off_dia_ana/diag_product_ana
    except:
        print("diag_product_ana is zero")
        diag_product_ana += 1e-8
        M_th_ratio_ana = off_dia_ana/diag_product_ana
    for index, sub_tensor in enumerate(M_th_ana):
        if M_th_ratio_ana[index] > 0.1:
            print("M_th_ratio_ana > 0.1:", M_th_ratio_ana[index])
            print("q:", q_grid_flat[index])
            print("M_th_ana:\n", sub_tensor)
            print("J_h_ana:\n", J_h_ana[index])
            break


    M_th_ratio_grid = M_th_ratio.view(q1_grid.shape)
    M_th_ratio_grid_np = np.abs(M_th_ratio_grid.detach().cpu().numpy())
    M_th_ratio_grid_np_capped = np.copy(M_th_ratio_grid_np)
    M_th_ratio_grid_np_capped[M_th_ratio_grid_np_capped >= 5] = 5
    
    M_th_ratio_ana_grid = M_th_ratio_ana.view(q1_grid.shape)
    M_th_ratio_ana_grid_np = np.abs(M_th_ratio_ana_grid.detach().cpu().numpy())
    q1_grid_np = q1_grid.numpy()
    q2_grid_np = q2_grid.numpy()
    
    plot_title = "Ratio of off-diagonal to diagonal entries" + str(epoch + 1)
    title_1 = r"Learned $M_{theta}$ ratio (capped)"
    title_2 = r"Learned $M_{theta}$ ratio (full)"
    xlabel = "$q_1$ (rad)"
    ylabel = "$q_2$ (rad)"
    zlabel = "$Ratio$ (-)"
    z_limits = (0, 5)
    
    plot_3d_double(q1_grid_np, q2_grid_np, M_th_ratio_grid_np_capped, M_th_ratio_grid_np, 
                   plot_title, title_1, title_2, xlabel, ylabel, zlabel, z_limits)
    

def plot_decoupling_inv(model, device, rp, epoch):
    
    #Obtain [q1,q1]-grid and flatten
    q1_grid, q2_grid = plot_data()
    q_grid_flat = torch.stack([q1_grid.flatten(), q2_grid.flatten()], dim=-1).to(device)  # Shape: (N, 2)
    
    J_h_inv, q_hat = model(q_grid_flat)

    J_h_inv_trans = J_h_inv.transpose(1,2).to(device)
    
    matrices_vmap = torch.vmap(dynamics.dynamical_matrices, 
                                   in_dims=(None, 0, 0))

    
    # Inputting q as q_d. This is not pretty but it doesn't matter since we only care about M_q
    M_q, C_q, G_q = matrices_vmap(rp, q_grid_flat, q_grid_flat)
    
        
    M_th, C_th, G_th = transforms.transform_dynamical_from_inverse(M_q, C_q, G_q, J_h_inv, J_h_inv_trans)
    #M_th_ana, C_th_ana, G_th_ana = transforms.transform_dynamical_matrices(M_q, C_q, G_q, J_h_ana, device)


    matrices_th_ana_vmap = torch.vmap(dynamics.dynamical_matrices_th, 
                                   in_dims=(None, 0, 0))
    M_th_ana, C_th_ana, G_th_ana = matrices_th_ana_vmap(rp, q_grid_flat, q_grid_flat)
    
    off_dia = M_th[:, 0, 1]
    diag_elements = M_th_ana[:, [0, 1], [0, 1]]
    diag_product = torch.sqrt(diag_elements[:, 0] * diag_elements[:, 1])
    try:
        M_th_ratio = off_dia/diag_product
    except:
        print("diag_product is zero")
        diag_product += 1e-8
        M_th_ratio = off_dia/diag_product


    off_dia_ana = M_th_ana[:, 0, 1]
    diag_elements_ana = M_th_ana[:, [0, 1], [0, 1]] 
    diag_product_ana = torch.sqrt(diag_elements_ana[:, 0] * diag_elements_ana[:, 1])

    try:
        M_th_ratio_ana = off_dia_ana/diag_product_ana
    except:
        print("diag_product_ana is zero")
        diag_product_ana += 1e-8
        M_th_ratio_ana = off_dia_ana/diag_product_ana
    for index, sub_tensor in enumerate(M_th_ana):
        if M_th_ratio_ana[index] > 0.1:
            print("M_th_ratio_ana > 0.1:", M_th_ratio_ana[index])
            print("q:", q_grid_flat[index])
            print("M_th_ana:\n", sub_tensor)
            print("J_h_ana:\n", J_h_ana[index])
            break


    M_th_ratio_grid = M_th_ratio.view(q1_grid.shape)
    M_th_ratio_grid_np = np.abs(M_th_ratio_grid.detach().cpu().numpy())
    M_th_ratio_grid_np_capped = np.copy(M_th_ratio_grid_np)
    M_th_ratio_grid_np_capped[M_th_ratio_grid_np_capped >= 5] = 5
    
    M_th_ratio_ana_grid = M_th_ratio_ana.view(q1_grid.shape)
    M_th_ratio_ana_grid_np = np.abs(M_th_ratio_ana_grid.detach().cpu().numpy())
    q1_grid_np = q1_grid.numpy()
    q2_grid_np = q2_grid.numpy()
    
    plot_title = "Ratio of off-diagonal to diagonal entries" + str(epoch + 1)
    title_1 = r"Learned $M_{theta}$ ratio (capped)"
    title_2 = r"Learned $M_{theta}$ ratio (full)"
    xlabel = "$q_1$ (rad)"
    ylabel = "$q_2$ (rad)"
    zlabel = "$Ratio$ (-)"
    z_limits = (0, 5)
    
    plot_3d_double(q1_grid_np, q2_grid_np, M_th_ratio_grid_np_capped, M_th_ratio_grid_np, 
                   plot_title, title_1, title_2, xlabel, ylabel, zlabel, z_limits)
    