import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import { Brain, Users, Target, Award, ArrowLeft, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

const About = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center">
              <Brain className="w-7 h-7 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">SkillBridge AI</h1>
              <p className="text-xs text-muted-foreground font-medium">ŠKODA Career Intelligence</p>
            </div>
          </div>

          <Button 
            variant="ghost" 
            onClick={() => navigate("/")}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center max-w-4xl mx-auto space-y-6"
          >
            <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium">
              <Sparkles className="w-4 h-4" />
              About SkillBridge AI
            </div>
            
            <h1 className="text-5xl lg:text-6xl font-bold text-foreground">
              Empowering Careers Through
              <span className="block bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                AI Intelligence
              </span>
            </h1>
            
            <p className="text-xl text-muted-foreground leading-relaxed">
              SkillBridge AI is ŠKODA's next-generation career development platform, 
              designed to transform how employees and managers approach skill development, 
              career planning, and organizational growth.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="text-center space-y-6 mb-16"
            >
              <h2 className="text-4xl font-bold text-foreground">Our Mission</h2>
              <p className="text-lg text-muted-foreground">
                To revolutionize career development at ŠKODA by providing AI-powered insights 
                that help every employee reach their full potential while driving organizational excellence.
              </p>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
              >
                <Card className="p-8 h-full hover:shadow-lg transition-shadow">
                  <Target className="w-12 h-12 text-primary mb-4" />
                  <h3 className="text-2xl font-bold text-foreground mb-3">For Employees</h3>
                  <p className="text-muted-foreground">
                    Gain clarity on your skill strengths, identify development areas, 
                    receive personalized learning recommendations, and map your ideal career trajectory 
                    with AI-powered guidance.
                  </p>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <Card className="p-8 h-full hover:shadow-lg transition-shadow">
                  <Users className="w-12 h-12 text-secondary mb-4" />
                  <h3 className="text-2xl font-bold text-foreground mb-3">For Managers</h3>
                  <p className="text-muted-foreground">
                    Understand team capabilities, identify skill gaps, make data-driven development 
                    decisions, and optimize team performance with comprehensive analytics and insights.
                  </p>
                </Card>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-4xl font-bold text-foreground text-center mb-12"
            >
              What Makes Us Different
            </motion.h2>

            <div className="space-y-8">
              {[
                {
                  icon: Brain,
                  title: "AI-Powered Intelligence",
                  description: "Advanced algorithms analyze your skills, experience, and goals to provide personalized recommendations and insights."
                },
                {
                  icon: Award,
                  title: "Real Data Integration",
                  description: "Connected to ŠKODA's HR systems, pulling real employee data, course information, and organizational structures for accurate insights."
                },
                {
                  icon: Target,
                  title: "Career Path Planning",
                  description: "Visualize multiple career trajectories, understand requirements for each path, and get guided development plans."
                },
                {
                  icon: Users,
                  title: "Team Analytics",
                  description: "Managers gain comprehensive visibility into team capabilities, skill distributions, and development priorities."
                }
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                >
                  <Card className="p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <feature.icon className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-foreground mb-2">{feature.title}</h3>
                        <p className="text-muted-foreground">{feature.description}</p>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-primary text-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center max-w-3xl mx-auto space-y-6"
          >
            <h2 className="text-4xl font-bold">Ready to Transform Your Career?</h2>
            <p className="text-xl text-white/90">
              Join hundreds of ŠKODA employees already using SkillBridge AI to accelerate their career growth.
            </p>
            <Button 
              size="lg"
              variant="secondary"
              onClick={() => navigate("/login")}
              className="text-lg px-8"
            >
              Get Started Today
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center text-muted-foreground">
            <p className="text-sm">
              © 2025 ŠKODA Auto. SkillBridge AI - Internal Career Development Platform
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default About;
