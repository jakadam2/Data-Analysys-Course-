import math
import random
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import scipy.special

class SGD():
    
    def __init__(self, m_good, m_bad, m=[1,1], labels=[-1, 1], prior=[1/2, 1/2], n_iterates=None, learning_rate = 0.01, decay=False, early_stopping=False, s=1, N=100):
        """
        Input:
        - m: mean of the x that will generates when label is +1
        - labels: the two label
        - prior: list that contains prior of -1 and +1
        - n_iterates: is used only in online application. Represent the max number of iterations that will be performed
        - learning rate: in case of decaying step-size, that is the tau. In constant step-size is the mu
        - decay: if decay is false the learning rate remains constant. In contrast, if is true th learning rate will be (learning rate)/(i+1)
        - early_stopping: if is a number -> if J don't change more than a constant between two iterations, the for-each will stop
        - s: mini-batch size. If s=1, will be performed SGD with 
        - N: size of dataset
        """
        self._m_bad = m_bad
        self._m_good = m_good
        self._m = m
        self._labels = labels
        self._prior = prior
        # value of the optimal parameters of beta
        self._best_beta = [(-self._norm(m)**2)/2 + math.log(prior[1]/prior[0])] + m
        self._learning_rate = learning_rate
        self._decay = decay
        self._early_stopping = early_stopping
        self._s = s
        self._N = N
        self._n_iterates = n_iterates
        self._beta = None
        self._J = None
        self._Q = None
        self._MSE = None
        self._beta_values = None
        

    def run(self):
        """
        This method run the SGD
        """

        stop = 0

        # Inizializate beta
        beta = list(range(len(self._m) + 1))
        for i in range(len(beta)):
            beta[i] = random.random()
        # beta =[random.random()] + [0] * len(self._m)
            
        learning_rate = self._learning_rate
        # Generate data
        labels, data = self.twotranches(self._N, self._m_bad, self._m_good)
        n_iterates = math.ceil(len(labels)/self._s)
        self._n_iterates = n_iterates

        self._J = [None] * n_iterates
        # Because the loss function Q is defined on a sample of dataset
        self._Q = [None] * self._N
        self._MSE = [None] * n_iterates
        self._beta_values = [None] * n_iterates
        x_J = []
        y_J = []

        for i in range(n_iterates):
            y, x = labels[i*self._s:(i+1)*self._s], data[i*self._s:(i+1)*self._s]
            x_J = x_J + x
            y_J = y_J + y

            # Calculate the gradient
            grad = self._calculate_gradient(y, x, beta)
            # Update beta
            beta = self._update_beta(beta, grad, learning_rate)
            # Calculate actual J
            #self._J[i] = self._calculate_J(y_J, x_J, beta)
            # Calculate Q
            # for k in range(len(y)):
            #     self._Q[i*self._s+k] = math.log(1 + math.exp(-y[k]*self._dot_product(x[k], beta)))
            # Calculate MSE
            
            self._beta_values[i] = beta.copy()
            #self._MSE[i] = self._calculate_MSE(beta)

            # If early stopping must be performed
            if self._early_stopping != False:
                if i!=0 and (abs(self._J[i]-self._J[i-1])<=0.00001):
                    stop = stop+1
                    if stop >= self._early_stopping:
                        print("Stop at iteretion number", i)
                        break
                else:
                    stop = 0
            # If decay must be performed
            if self._decay:
                learning_rate = self._learning_rate/(i+1)
        self._beta = beta


        

    def plot_costs(self):
        """
        Plot graphs of the cost function J, loss function Q and MSE
        """
        plt.plot(list(range(self._n_iterates)), self._J, label="J")
        plt.xlabel("i")
        plt.ylabel("J")
        plt.legend()
        plt.show()
        plt.plot(list(range(self._N)), self._Q, label="Q")
        plt.xlabel("N")
        plt.ylabel("Q")
        plt.legend()
        plt.show()
        plt.plot(list(range(self._n_iterates)), self._MSE, label="MSE")
        plt.xlabel("i")
        plt.ylabel("MSE")
        plt.legend()
        plt.show()

    def test_beta(self, beta=None, n=100):
        """
        This methods generate n point and tests beta's ability to classify these points correctly
        """
        if beta == None:
            beta = self._beta
        
        # Plot estimated beta
        x0 = np.linspace(-5, 5, 100)
        x1 = (-beta[0] - beta[1] * x0) / beta[2]
        plt.plot(x0, x1, label="estimated beta")
        plt.legend()

        # Plot best beta
        x1 = (-self._best_beta[0] - self._best_beta[1] * x0) / self._best_beta[2]
        plt.plot(x0, x1, label="best beta")
        plt.legend()

        TP = []
        TN = []
        FN = []
        FP = []
        y, x = self._generate_data(n)
        for i in range(n):
            
            f_x = 0
            for k in range(len(x[i])):
                f_x = f_x + beta[k]*x[i][k]
            if y[i] == 1:
                if f_x > 0:
                    TP.append([x[i][1], x[i][2]])
                else:
                    FN.append([x[i][1], x[i][2]])
            else:
                if f_x > 0:
                    FP.append([x[i][1], x[i][2]])
                else:
                    TN.append([x[i][1], x[i][2]])

        self._scatter_points(TN, "black", "TN")
        self._scatter_points(TP, "green", "TP")
        self._scatter_points(FP, "red", "FP")
        self._scatter_points(FN, "blue", "FN")

        plt.show()

    def _scatter_points(self, points, color, label):
        x0 = [point[0] for point in points]
        x1 = [point[1] for point in points]
        plt.scatter(x0, x1, color=color, label=label)
        plt.legend()


    def _calculate_J(self, y_J, x_J, beta):
        """
        J = log(1 + exp(-y*beta*x))
        """
        values = 0
        for i in range(len(y_J)):
            values = values + math.log(1 + math.exp(-y_J[i]*self._dot_product(x_J[i], beta)))
        return values/len(y_J)

    def _calculate_gradient(self, y, x, beta):
        """
        dJ/dbeta = -y*x*(exp(-y*beta*x)/(1+exp(-y*beta*x))) = -y*x*(1/(1+exp(y*beta*x)))
        If s, the batch size, is more than one -> will be performed the arithmetic mean
        """
        s = len(y)
        grad = [0] * len(x[0])
        for k in range(s):
            const = 1/(1+math.exp(y[k]*self._dot_product(x[k], beta)))
            
            for i in range(len(grad)):
                grad[i] = grad[i] - (y[k]*x[k][i]*const)
        for i in range(len(grad)):
            grad[i] = grad[i]/s
        return grad

    def _update_beta(self, beta, grad, learning_rate):
        """
        This method update beta
        """
        for i in range(len(beta)):
            beta[i] = beta[i] - learning_rate*grad[i]
        return beta

    # def _new_sample(self):
    #     label = random.choice(self._labels)
    #     x = list(range(len(self._m)))
    #     if label == 1:
    #         m = self._m
    #     else:
    #         m = [0] * len(self._m)
    #     for i in range(len(self._m)):
    #         x[i] = np.random.normal(m[i], 1)
    #     x = [1] + x
    #     return label, x

    def _generate_data(self, n):
        """
        Input:
        - n: number of data will be generated
        Output:
        - y: list of n labels
        - x: data associated to the labels
        """
        x = [0] * n
        label = [0] * n
        for k in range(n):
            label[k] = random.choice(self._labels)
            x[k] = list(range(len(self._m)))
            if label[k] == 1:
                m = self._m
            else:
                m = [0] * len(self._m)
            for i in range(len(self._m)):
                x[k][i] = np.random.normal(m[i], 1)
            x[k] = [1] + x[k]
        return label, x
    
    def _dot_product(self, x1, x2):
        """
        Perform the dot product between x1 and x2.
        """
        value = 0
        for i in range(len(x1)):
            value = value + x1[i]*x2[i]
        return value

    def _norm(self, values):
        """
        Perform norm on a list of numbers
        """
        return math.sqrt(sum(x**2 for x in values))
    
    def _calculate_MSE(self, beta):
        """
        E[∥βi-β∥^2]
        """
        err = [0] *len(beta)
        for i in range(len(beta)):
            err[i] = beta[i] - self._best_beta[i]
        return self._norm(err)**2





    def plot_ROC(self, nMC=5, n=100, step=0.01):
        """
        Input:
        - nMC: run MonteCarlo
        - n: number of sample
        - step: step for generate alpha
        """
        alphas = np.arange(0, 1+step, step).tolist()
        gammas = self._gamma_calculate(alphas)
        one_minus_beta, one_minus_best_beta = self._one_minus_beta_calculate(alphas)
        TP = [[0 for j in range(len(alphas))] for i in range(nMC)]
        TN = [[0 for j in range(len(alphas))] for i in range(nMC)]
        FP = [[0 for j in range(len(alphas))] for i in range(nMC)]
        FN = [[0 for j in range(len(alphas))] for i in range(nMC)]

        TPR_run = [[0 for j in range(len(alphas))] for i in range(nMC)]
        FPR_run = [[0 for j in range(len(alphas))] for i in range(nMC)]

        TPR = [0] * len(alphas)
        FPR = [0] * len(alphas)
        for run in range(nMC):
            y, x = self._generate_data(n)
            for k in range(n):
                f = 0
                for i in range(len(self._m)):
                    f = f + self._beta[i+1]*x[k][i+1]
                for i in range(len(alphas)):
                    if y[k] == -1:
                        if f < gammas[i]:
                            TN[run][i] = TN[run][i] + 1
                        else:
                            FP[run][i] = FP[run][i] + 1
                    else:
                        if f > gammas[i]:
                            TP[run][i] = TP[run][i] + 1
                        else:
                            FN[run][i] = FN[run][i] + 1
            for i in range(len(alphas)):
                if FP[run][i] + TN[run][i] != 0:
                    FPR_run[run][i] =  FP[run][i] / (FP[run][i] + TN[run][i])
                else:
                    print("Divisione per zero nella FPR_run")
                    FPR_run[run][i] = 0
                
                if TP[run][i] + FN[run][i] != 0:
                    TPR_run[run][i] = TP[run][i] / (TP[run][i] + FN[run][i])
                else:
                    print("Divisione per zero nella TPR_run")
                    TPR_run[run][i] = 0
        
        for i in range(len(alphas)):
            fpr = 0
            tpr = 0
            for run in range(nMC):
                fpr = fpr + FPR_run[run][i]
                tpr = tpr + TPR_run[run][i]
            TPR[i] = tpr/(run+1)
            FPR[i] = fpr/(run+1)
        plt.plot(FPR, TPR, label="estimated ROC with estimated beta")
        plt.plot(alphas, one_minus_beta, label="best ROC with estimated beta")
        plt.plot(alphas, one_minus_best_beta, label="best ROC with best beta")
        plt.legend()
        plt.show()

    def _gamma_calculate(self, alphas):
        """
        Calculate value of gamma for eache value of alpha.
        """
        gammas = [0] * len(alphas)
        den = 0
        for i in range(1, len(self._beta)):
            den = den + (self._beta[i]**2)
        den = math.sqrt(den)
        #const = math.log(self._prior[1]/self._prior[0]) - self._beta[0]
        for i in range(len(alphas)):
            gammas[i] = self._inverse_Q_function(alphas[i])*den
        return gammas
    
    def _one_minus_beta_calculate(self, alphas):
        """
        Calculate best value of beta for each value of alpha.
        """
        betas = [0] * len(alphas)
        best_betas = [0] * len(alphas)
        num = 0
        den = 0
        best_num = 0
        best_den = 0
        for i in range(0, len(self._m)):
            num = num + self._beta[i+1]*self._m[i] 
            den = den + (self._beta[i+1]**2)
            best_num = best_num + self._best_beta[i+1]*self._m[i] 
            best_den = best_den + (self._best_beta[i+1]**2)
        const = num/math.sqrt(den)
        best_const = best_num/math.sqrt(best_den)
        for i in range(len(alphas)):
            betas[i] = self._Q_function((self._inverse_Q_function(alphas[i]) - const))
            best_betas[i] = self._Q_function((self._inverse_Q_function(alphas[i]) - best_const))
        return betas, best_betas

    def _inverse_Q_function(self, x):
        """
        Calculate inverse of Q function.
        """
        return norm.ppf(1 - x)
    
    def _Q_function(self, x):
        """
        Calculate Q function.
        """
        return 0.5 * scipy.special.erfc(x / (2**0.5))



    # def run_online(self):
    #     """
    #     If you have an algorithm online, run this.
    #     """
    #     stop = 0

    #     # Inizializate beta
    #     beta = list(range(len(self._m) + 1))
    #     for i in range(len(beta)):
    #         beta[i] = random.random()
            
    #     learning_rate = self._learning_rate

    #     n_iterates = math.ceil(self._n_iterates/self._s)
    #     self._n_iterates = n_iterates

    #     self._J = [None] * n_iterates
    #     # Because the loss function Q is defined on a sample of dataset
    #     self._N = n_iterates*self._s
    #     self._Q = [None] * self._N
    #     self._MSE = [None] * n_iterates
    #     self._beta_values = [None] * n_iterates
    #     x_J = []
    #     y_J = []

    #     for i in range(n_iterates):
    #         y, x = self._generate_data(self._s)
    #         x_J = x_J + x
    #         y_J = y_J + y

    #         # Calculate the gradient
    #         grad = self._calculate_gradient(y, x, beta)
    #         # Update beta
    #         beta = self._update_beta(beta, grad, learning_rate)
    #         # Calculate actual J
    #         self._J[i] = self._calculate_J(y_J, x_J, beta)
    #         # Calculate Q
    #         for k in range(len(y)):
    #             self._Q[i*self._s+k] = math.log(1 + math.exp(-y[k]*self._dot_product(x[k], beta)))
    #         # Calculate MSE
    #         self._beta_values[i] = beta
    #         self._MSE[i] = self._calculate_MSE(beta)

    #         # If early stopping must be performed
    #         if self._early_stopping != False:
    #             if i!=0 and (abs(self._J[i]-self._J[i-1])<=0.00001):
    #                 stop = stop+1
    #                 if stop >= self._early_stopping:
    #                     print("Stop at iteretion number", i)
    #                     break
    #             else:
    #                 stop = 0
    #         # If decay must be performed
    #         if self._decay:
    #             learning_rate = self._learning_rate/(i+1)
    #     self._beta = beta

    def plot_posterior(self, theta, m=[1]):
        self._m = m
        m = self._m[0]
        x = np.arange(-3, 6+0.01, 0.01).tolist()
        p = [0]*len(x)
        for i in range(len(x)):
            p[i] = 1/(1+math.exp(-theta*(x[i]*m-(m**2)/2)))

        plt.plot(x, p)
        plt.xlabel("x")
        plt.ylabel("p("+str(theta)+"|x)")
        plt.title("m = "+str(m))

        plt.axvline(x=0, color='black')
        plt.axvline(x=m, color='red')


        plt.show()

    def return_posterior(self, theta, x, m=1):

        p = 1/(1+math.exp(-theta*(x*m-(m**2)/2)))
        return p


    def scatter_data(self, m, n=20):
        self._m = m
        y, x = self._generate_data(n)
        for i in range(len(y)):
            if y[i] == -1:
                color = "black"
            else:
                color = "red"
            plt.scatter(x[i][1], 0, color=color)
        plt.show()


    def MAP_rule(self, m, nMC=100, n=100):
        pr_err = [0] * nMC
        self._m = [m]
        for run in range(nMC):
            y, x = self._generate_data(n)
            pr_neg = 0
            pr_pos = 0
            for i in range(len(y)):
                p = self.return_posterior(1, x[i][1], m) # p(theta|x)
                if p == 0:
                    print("a")
                f_x = math.log(p/(1-p))
                if f_x > 0:
                    if y[i] == -1:
                        pr_neg = pr_neg + 1
                else:
                    if y[i] == 1:
                        pr_pos = pr_pos + 1
            pr_neg = pr_neg/len(y)
            pr_pos = pr_pos/len(y)
            pr_err[run] = 1/2*(pr_neg + pr_pos)
        return sum(pr_err)/nMC
    
    def twotranches(self, n, m_bad, m_good):
        self._m = [m_good]
        y_good, x_good = self._generate_data(int(n/2))
        self._m = [m_bad]
        y_bad, x_bad= self._generate_data(int(n/2))
        return y_good+y_bad, x_good+x_bad

    def plot_beta(self):
        plt.figure()
        beta0 = [0]*len(self._beta_values)
        for i in range(len(self._beta_values)):
            beta0[i] = self._beta_values[i][0]
        plt.plot(range(len(self._beta_values)), beta0)
        plt.show()
        beta1 = [0]*len(self._beta_values)
        for i in range(len(self._beta_values)):
            beta1[i] = self._beta_values[i][1]
        plt.plot(range(len(self._beta_values)), beta1)
        plt.show()

    def find_betas(self):
        m = 30
        mean_prev = 0
        for k in range(m):
            mean_prev = mean_prev + self._beta_values[k][0]
        mean_prev = mean_prev/m
        for i in range(1, math.ceil(len(self._beta_values)/m)):
            if i*m+k<len(self._beta_values):
                mean_next = 0
                for k in range(m):
                    mean_next = mean_next + self._beta_values[i*m+k][0]
                mean_next = mean_next/m
                if mean_prev-mean_next > 2:
                    print(i*m)
                    
                mean_prev = mean_next

m_bad = 0.5
m_good = 5
s = SGD(m_good, m_bad,  N=5000, m=[1], learning_rate=0.9)

# s.plot_posterior(1, m=[m_bad])
# s.plot_posterior(1, m=[m_good])

# s.scatter_data([m_good])

# s.scatter_data([m_bad])
# print()
# print("The error probability with mgood is",s.MAP_rule(5, n=100))
# print("The error probability with mbad is",s.MAP_rule(-5, n=100))
# print()


s.run()

# s.find_betas()
s.plot_beta()
# s.plot_costs()
# s.test_beta() # You can launch it only if you have len(m)==2
# s.plot_ROC(nMC=10, n=1000)